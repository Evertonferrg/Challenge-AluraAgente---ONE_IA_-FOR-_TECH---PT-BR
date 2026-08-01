import pandas as pd
import os
import random
from datetime import date, datetime, timedelta
from . import email_utils

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTES_PATH = os.path.join(BASE_DIR, "data", "clientes.csv")
BOLETOS_PATH = os.path.join(BASE_DIR, "data", "boletos.csv")
CHAMADOS_PATH = os.path.join(BASE_DIR, "data", "chamados.csv")

HOJE = date(2026, 7, 26)

MAX_ITENS_LISTA = 5  # limita listas longas para economizar tokens no retorno à IA

TAXA_MULTA_ATRASO_PCT = 2.0
TAXA_JUROS_DIARIO_PCT = 0.033
FORMAS_VALIDAS = ["Boleto", "PIX", "Cartão de Crédito", "Transferência (TED)"]


# ---------- helpers internos (não expostos como tools) ----------

def _carregar_clientes() -> pd.DataFrame:
    return pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})

def _salvar_clientes(df: pd.DataFrame):
    df.to_csv(CLIENTES_PATH, index=False)

def _carregar_boletos() -> pd.DataFrame:
    df = pd.read_csv(BOLETOS_PATH, dtype={"cpf_cliente": str})
    df["data_emissao"] = pd.to_datetime(df["data_emissao"]).dt.date
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"]).dt.date
    return df

def _salvar_boletos(df: pd.DataFrame):
    df.to_csv(BOLETOS_PATH, index=False)

def _carregar_chamados() -> pd.DataFrame:
    if not os.path.exists(CHAMADOS_PATH):
        return pd.DataFrame(columns=["id_chamado", "cpf_cliente", "id_boleto", "motivo", "data_abertura", "status"])
    return pd.read_csv(CHAMADOS_PATH, dtype=str)

def _salvar_chamados(df: pd.DataFrame):
    df.to_csv(CHAMADOS_PATH, index=False)

def _limitar(lista: list, chave_total: str = "total_registros") -> dict:
    """Corta listas longas antes de devolver à IA, mantendo o total real."""
    return {
        "itens": lista[:MAX_ITENS_LISTA],
        chave_total: len(lista),
        "truncado": len(lista) > MAX_ITENS_LISTA,
    }


# ---------- tools expostas ao agente ----------

def identificar_cliente_por_cpf(cpf: str) -> dict:
    """Busca dados cadastrais do cliente pelo CPF."""
    clientes = _carregar_clientes()
    cliente = clientes[clientes["cpf"] == cpf]
    if cliente.empty:
        return {"encontrado": False, "mensagem": f"CPF {cpf} não encontrado."}
    return {"encontrado": True, **cliente.iloc[0].to_dict()}


def analisar_vencimento_boletos(cpf: str) -> dict:
    """Lista boletos pendentes e vencidos do cliente."""
    boletos = _carregar_boletos()
    do_cliente = boletos[boletos["cpf_cliente"] == cpf].copy()
    if do_cliente.empty:
        return {"encontrado": False, "mensagem": f"Sem boletos para o CPF {cpf}."}

    pendentes = do_cliente[do_cliente["status"] == "Pendente"].copy()
    vencidos = do_cliente[do_cliente["status"] == "Vencido"].copy()
    pendentes["dias_para_vencer"] = pendentes["data_vencimento"].apply(lambda d: (d - HOJE).days)
    vencidos["dias_em_atraso"] = vencidos["data_vencimento"].apply(lambda d: (HOJE - d).days)

    pend_list = pendentes[["id_boleto", "valor", "data_vencimento", "dias_para_vencer"]].to_dict("records")
    venc_list = vencidos[["id_boleto", "valor", "data_vencimento", "dias_em_atraso"]].to_dict("records")

    return {
        "encontrado": True,
        "pendentes": _limitar(pend_list, "total_pendentes"),
        "vencidos": _limitar(venc_list, "total_vencidos"),
    }


def verificar_notas_vencidas(cpf: str) -> dict:
    """Retorna boletos vencidos e valor total em atraso do cliente."""
    resultado = analisar_vencimento_boletos(cpf)
    if not resultado.get("encontrado"):
        return resultado
    venc = resultado["vencidos"]
    valor_total = round(sum(b["valor"] for b in venc["itens"]), 2)
    return {"encontrado": True, "vencidos": venc, "valor_total_vencidos_pagina": valor_total}


def verificar_desconto_pagamento_antecipado(id_boleto: str) -> dict:
    """Calcula valor com desconto se o boleto for pago antes do vencimento."""
    boletos = _carregar_boletos()
    clientes = _carregar_clientes()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    b = boleto.iloc[0]
    if b["status"] != "Pendente":
        return {"encontrado": True, "elegivel": False, "mensagem": f"Status '{b['status']}' não é elegível para desconto."}

    cliente = clientes[clientes["cpf"] == b["cpf_cliente"]].iloc[0]
    desconto_pct = float(cliente["desconto_pagamento_antecipado_pct"])
    valor_original = float(b["valor"])
    valor_com_desconto = round(valor_original * (1 - desconto_pct / 100), 2)

    return {
        "encontrado": True,
        "elegivel": True,
        "id_boleto": id_boleto,
        "valor_original": valor_original,
        "valor_com_desconto": valor_com_desconto,
        "economia": round(valor_original - valor_com_desconto, 2),
    }


def verificar_credito(cpf: str) -> dict:
    """Verifica limite, uso e disponibilidade de crédito do cliente."""
    cliente = identificar_cliente_por_cpf(cpf)
    if not cliente["encontrado"]:
        return cliente
    limite = float(cliente["limite_credito"])
    usado = float(cliente["credito_utilizado"])
    return {
        "encontrado": True,
        "cliente": cliente["nome"],
        "status_credito": cliente["status_credito"],
        "credito_disponivel": round(limite - usado, 2),
        "percentual_utilizado": round((usado / limite) * 100, 1) if limite else 0,
    }


def emitir_segunda_via_boleto(id_boleto: str, enviar_por_email: bool = False, email: str = None) -> dict:
    """Emite 2ª via do boleto; opcionalmente envia por e-mail ao cliente."""
    boletos = _carregar_boletos()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    b = boleto.iloc[0]
    if b["status"] == "Pago":
        return {"encontrado": True, "emitido": False, "mensagem": f"Boleto {id_boleto} já pago."}

    resultado = {
        "encontrado": True,
        "emitido": True,
        "id_boleto": id_boleto,
        "valor": float(b["valor"]),
        "linha_digitavel": b["linha_digitavel"],
    }

    if enviar_por_email:
        clientes = _carregar_clientes()
        cliente = clientes[clientes["cpf"] == b["cpf_cliente"]].iloc[0]
        destino = email or cliente["email"]
        corpo = (
            f"Olá, {cliente['nome']},\n\nSegue a 2ª via do boleto {id_boleto}.\n"
            f"Valor: R$ {float(b['valor']):.2f}\nLinha digitável: {b['linha_digitavel']}\n\n"
            f"Atenciosamente,\nPetroMax Química"
        )
        envio = email_utils.enviar_email(destino, f"2ª via do boleto {id_boleto} - PetroMax Química", corpo)
        resultado["enviado_para"] = destino
        resultado["envio_email"] = envio

    return resultado


def alterar_forma_pagamento(id_boleto: str, nova_forma: str) -> dict:
    """Altera a forma de pagamento de um boleto (Boleto/PIX/Cartão/TED)."""
    if nova_forma not in FORMAS_VALIDAS:
        return {"sucesso": False, "mensagem": f"Forma inválida. Opções: {', '.join(FORMAS_VALIDAS)}."}

    boletos = _carregar_boletos()
    idx = boletos.index[boletos["id_boleto"] == id_boleto]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    boletos.loc[idx, "forma_pagamento"] = nova_forma
    _salvar_boletos(boletos)
    return {"sucesso": True, "mensagem": f"Boleto {id_boleto} alterado para {nova_forma}."}


def alterar_data_vencimento(id_boleto: str, nova_data: str) -> dict:
    """Altera data de vencimento do boleto (formato AAAA-MM-DD)."""
    try:
        nova_data_dt = datetime.strptime(nova_data, "%Y-%m-%d").date()
    except ValueError:
        return {"sucesso": False, "mensagem": "Data inválida. Use AAAA-MM-DD."}

    boletos = _carregar_boletos()
    idx = boletos.index[boletos["id_boleto"] == id_boleto]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    boletos.loc[idx, "data_vencimento"] = nova_data_dt
    if (boletos.loc[idx, "status"] == "Vencido").any():
        boletos.loc[idx, "status"] = "Pendente"
    _salvar_boletos(boletos)
    return {"sucesso": True, "mensagem": f"Boleto {id_boleto} agora vence em {nova_data}."}


def gerar_relatorio_cobranca(cpf: str) -> dict:
    """Resumo de cobrança do cliente: crédito, vencidos e pendentes."""
    credito = verificar_credito(cpf)
    if not credito.get("encontrado"):
        return credito
    vencimentos = analisar_vencimento_boletos(cpf)
    return {
        "encontrado": True,
        "cliente": credito["cliente"],
        "status_credito": credito.get("status_credito"),
        "credito_disponivel": credito["credito_disponivel"],
        "pendentes": vencimentos["pendentes"],
        "vencidos": vencimentos["vencidos"],
    }


def calcular_juros_multa_atraso(id_boleto: str) -> dict:
    """Calcula multa e juros de mora de um boleto vencido."""
    boletos = _carregar_boletos()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    b = boleto.iloc[0]
    if b["status"] != "Vencido":
        return {"encontrado": True, "aplica_encargos": False, "mensagem": f"Status '{b['status']}' sem encargos."}

    dias_atraso = (HOJE - b["data_vencimento"]).days
    valor_original = float(b["valor"])
    multa = round(valor_original * (TAXA_MULTA_ATRASO_PCT / 100), 2)
    juros = round(valor_original * (TAXA_JUROS_DIARIO_PCT / 100) * dias_atraso, 2)

    return {
        "encontrado": True,
        "aplica_encargos": True,
        "dias_atraso": dias_atraso,
        "valor_original": valor_original,
        "valor_atualizado": round(valor_original + multa + juros, 2),
    }


def consultar_historico_pagamento(cpf: str) -> dict:
    """Score de pagador do cliente com base no histórico de boletos."""
    boletos = _carregar_boletos()
    do_cliente = boletos[boletos["cpf_cliente"] == cpf].copy()
    if do_cliente.empty:
        return {"encontrado": False, "mensagem": f"Sem boletos para o CPF {cpf}."}

    pagos = do_cliente[do_cliente["status"] == "Pago"].copy()
    pagos["data_pagamento_dt"] = pd.to_datetime(pagos["data_pagamento"]).dt.date
    pagos_em_dia = pagos[pagos["data_pagamento_dt"] <= pagos["data_vencimento"]]
    vencidos_em_aberto = do_cliente[do_cliente["status"] == "Vencido"]
    pct = round(len(pagos_em_dia) / len(pagos) * 100, 1) if len(pagos) else None

    if len(vencidos_em_aberto) >= 3 or (pct is not None and pct < 50):
        score = "Inadimplente contumaz"
    elif len(vencidos_em_aberto) >= 1 or (pct is not None and pct < 80):
        score = "Atraso recorrente"
    else:
        score = "Bom pagador"

    return {"encontrado": True, "percentual_pontualidade": pct, "score_pagador": score}


def verificar_restricao_credito(cpf: str) -> dict:
    """Consulta restrição SPC/Serasa do cliente (dado simulado)."""
    cliente = identificar_cliente_por_cpf(cpf)
    if not cliente["encontrado"]:
        return cliente
    possui = cliente["restricao_spc_serasa"] == "Sim"
    return {"encontrado": True, "cliente": cliente["nome"], "possui_restricao": possui}


def bloquear_desbloquear_pedidos(cpf: str, acao: str) -> dict:
    """Bloqueia ou libera novos pedidos do cliente ('bloquear'/'desbloquear')."""
    if acao not in {"bloquear", "desbloquear"}:
        return {"sucesso": False, "mensagem": "Ação inválida. Use 'bloquear' ou 'desbloquear'."}

    clientes = _carregar_clientes()
    idx = clientes.index[clientes["cpf"] == cpf]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"CPF {cpf} não encontrado."}

    clientes.loc[idx, "pedidos_bloqueados"] = "Sim" if acao == "bloquear" else "Não"
    _salvar_clientes(clientes)
    verbo = "bloqueados" if acao == "bloquear" else "liberados"
    return {"sucesso": True, "mensagem": f"Pedidos do CPF {cpf} foram {verbo}."}


def negociar_parcelamento_divida(cpf: str, numero_parcelas: int) -> dict:
    """Parcela dívidas vencidas do cliente em novos boletos mensais (1-12x)."""
    if numero_parcelas < 1 or numero_parcelas > 12:
        return {"sucesso": False, "mensagem": "Parcelas devem ser entre 1 e 12."}

    boletos = _carregar_boletos()
    vencidos_idx = boletos.index[(boletos["cpf_cliente"] == cpf) & (boletos["status"] == "Vencido")]
    if len(vencidos_idx) == 0:
        return {"sucesso": False, "mensagem": f"Sem dívidas vencidas para o CPF {cpf}."}

    valor_total = float(boletos.loc[vencidos_idx, "valor"].sum())
    valor_atualizado = round(valor_total * (1 + TAXA_MULTA_ATRASO_PCT / 100), 2)
    valor_parcela = round(valor_atualizado / numero_parcelas, 2)
    boletos.loc[vencidos_idx, "status"] = "Renegociado"

    max_id = boletos["id_boleto"].str.extract(r"(\d+)").astype(int).max().iloc[0]
    novas_linhas = []
    for p in range(1, numero_parcelas + 1):
        max_id += 1
        novas_linhas.append({
            "id_boleto": f"BOL-{max_id:05d}", "cpf_cliente": cpf,
            "descricao": f"Parcela {p}/{numero_parcelas} - renegociação",
            "valor": valor_parcela, "data_emissao": HOJE.isoformat(),
            "data_vencimento": (HOJE + timedelta(days=30 * p)).isoformat(),
            "status": "Pendente", "forma_pagamento": "Boleto",
            "linha_digitavel": " ".join(str(random.randint(10000, 99999)) for _ in range(5)),
            "data_pagamento": "",
        })

    boletos = pd.concat([boletos, pd.DataFrame(novas_linhas)], ignore_index=True)
    _salvar_boletos(boletos)

    return {
        "sucesso": True,
        "valor_total_atualizado": valor_atualizado,
        "valor_por_parcela": valor_parcela,
        "novos_boletos": [n["id_boleto"] for n in novas_linhas],
    }


def abrir_chamado_contestacao(cpf: str, id_boleto: str, motivo: str) -> dict:
    """Abre chamado interno de contestação sobre uma cobrança."""
    chamados = _carregar_chamados()
    novo_id = f"CHM-{len(chamados) + 1:05d}"
    novo = {"id_chamado": novo_id, "cpf_cliente": cpf, "id_boleto": id_boleto,
            "motivo": motivo, "data_abertura": HOJE.isoformat(), "status": "Aberto"}
    chamados = pd.concat([chamados, pd.DataFrame([novo])], ignore_index=True)
    _salvar_chamados(chamados)
    return {"sucesso": True, "id_chamado": novo_id, "mensagem": f"Chamado {novo_id} aberto."}


def gerar_relatorio_inadimplencia_geral() -> dict:
    """Relatório geral de inadimplência da carteira, por faixa de atraso."""
    boletos = _carregar_boletos()
    vencidos = boletos[boletos["status"] == "Vencido"].copy()
    if vencidos.empty:
        return {"total_vencido": 0, "quantidade_boletos_vencidos": 0}

    vencidos["dias_atraso"] = vencidos["data_vencimento"].apply(lambda d: (HOJE - d).days)

    def faixa(dias):
        if dias <= 30: return "0-30 dias"
        if dias <= 60: return "31-60 dias"
        if dias <= 90: return "61-90 dias"
        return "90+ dias"

    vencidos["faixa_aging"] = vencidos["dias_atraso"].apply(faixa)
    aging = vencidos.groupby("faixa_aging")["valor"].agg(["count", "sum"]).round(2)
    aging_dict = {f: {"qtd": int(r["count"]), "valor": float(r["sum"])} for f, r in aging.iterrows()}

    return {
        "total_vencido": round(float(vencidos["valor"].sum()), 2),
        "quantidade_boletos_vencidos": len(vencidos),
        "clientes_inadimplentes": int(vencidos["cpf_cliente"].nunique()),
        "aging": aging_dict,
    }


def enviar_comprovante_pagamento(id_boleto: str, email: str = None) -> dict:
    """Envia comprovante de pagamento do boleto por e-mail."""
    boletos = _carregar_boletos()
    clientes = _carregar_clientes()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} não encontrado."}

    b = boleto.iloc[0]
    if b["status"] != "Pago":
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} ainda não pago."}

    cliente = clientes[clientes["cpf"] == b["cpf_cliente"]].iloc[0]
    destino = email or cliente["email"]
    corpo = (
        f"Olá, {cliente['nome']},\n\nConfirmamos o pagamento do boleto {id_boleto}.\n"
        f"Valor: R$ {float(b['valor']):.2f}\nData: {b['data_pagamento']}\n\nObrigado,\nPetroMax Química"
    )
    envio = email_utils.enviar_email(destino, f"Comprovante - boleto {id_boleto}", corpo)
    return {"sucesso": True, "enviado_para": destino, "envio_email": envio}


def enviar_alerta_vencimento_proximo(cpf: str, dias_antecedencia: int = 3) -> dict:
    """Envia por e-mail alerta de boletos vencendo nos próximos N dias."""
    cliente = identificar_cliente_por_cpf(cpf)
    if not cliente["encontrado"]:
        return cliente

    boletos = _carregar_boletos()
    proximos = boletos[
        (boletos["cpf_cliente"] == cpf) & (boletos["status"] == "Pendente")
        & (boletos["data_vencimento"] >= HOJE)
        & (boletos["data_vencimento"] <= HOJE + timedelta(days=dias_antecedencia))
    ]
    if proximos.empty:
        return {"encontrado": True, "enviado": False, "mensagem": f"Nada vence em {dias_antecedencia} dias."}

    lista = "\n".join(f"- {r.id_boleto}: R$ {r.valor:.2f}, vence em {r.data_vencimento}" for r in proximos.itertuples())
    corpo = (
        f"Olá, {cliente['nome']},\n\nVocê possui boleto(s) vencendo em breve:\n\n{lista}\n\n"
        f"Atenciosamente,\nPetroMax Química"
    )
    envio = email_utils.enviar_email(cliente["email"], "Lembrete: boleto(s) próximo(s) do vencimento", corpo)
    return {"encontrado": True, "enviado": True, "quantidade_boletos": len(proximos), "envio_email": envio}