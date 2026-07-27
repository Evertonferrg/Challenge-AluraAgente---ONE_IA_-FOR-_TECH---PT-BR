import pandas as pd
import os 
import random
import json
import datetime
from datetime import date
from datetime import date, datetime, timedelta
from random import randint

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENTES_PATH = os.path.join(BASE_DIR, "data", "clientes.csv")
BOLETOS_PATH = os.path.join(BASE_DIR, "data", "boletos.csv")

HOJE = date(2026, 7, 26)

def _carregar_clientes() -> pd.DataFrame:
    return pd.read_csv(CLIENTES_PATH, dtype={"cpf": str})

def identificar_cliente_por_cpf(cpf: str) -> dict:
    """Busca os dados cadastrais de um cliente a partir do CPF."""
    clientes = _carregar_clientes()
    cliente = clientes[clientes["cpf"] == cpf]

    if cliente.empty:
        return {"encontrado": False, "mensagem": f"Nenhum cliente encontrado com o CPF {cpf}."}

    c = cliente.iloc[0].to_dict()
    return {"encontrado": True, **c}


#Trabalhando com a tabela de boletos(mais complexa)

def _carregar_boletos() -> pd.DataFrame:
    df = pd.read_csv(BOLETOS_PATH, dtype={"cpf_cliente": str})
    df["data_emissao"] = pd.to_datetime(df["data_emissao"]).dt.date
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"]).dt.date
    return df

#Analisar vencimentos boletos

def analisar_vencimento_boletos(cpf: str) -> dict:
    """Lista boletos pendentes, próximos do vencimento e vencidos de um cliente."""
    boletos = _carregar_boletos()
    do_cliente = boletos[boletos["cpf_cliente"] == cpf].copy()

    if do_cliente.empty:
        return {"encontrado": False, "mensagem": f"Nenhum boleto encontrado para o CPF {cpf}."}
    
    pendentes = do_cliente[do_cliente["status"] == "Pendente"].copy()
    vencidos = do_cliente[do_cliente["status"] == "Vencido"].copy()

    pendentes["dias_para_vencer"] = pendentes["data_vencimento"].apply(lambda d: (d - HOJE).days)
    vencidos["dias_em_atraso"] = vencidos["data_vencimento"].apply(lambda d: (HOJE - d).days)

    return {
        "encontrado": True,
        "total_pendentes": len(pendentes),
        "total_vencidos": len(vencidos),
        "boletos_pendentes": pendentes[["id_boleto", "valor", "data_vencimento", "dias_para_vencer"]].to_dict("records"),
        "boletos_vencidos": vencidos[["id_boleto", "valor", "data_vencimento", "dias_em_atraso"]].to_dict("records"),
    }

#Verificar notas vencidas 
def verificar_notas_vencidas(cpf: str) -> dict:
    """Retorna apenas as notas/boletos vencidos e não pagos de um cliente, para fins de cobrança."""
    resultado = analisar_vencimento_boletos(cpf)
    if not resultado.get("encontrado"):
        return resultado
    
    return {
        "encontrado": True,
        "total_vencidos": resultado["total_vencidos"],
        "boletos_vencidos": resultado["boletos_vencidos"],
        "valor_total_vencidos": round(sum(b["valor"] for b in resultado["boletos_vencidos"]), 2),
    }

#Verificar descontos pagamento antecipado
def verificar_desconto_pagamento_antecipado(id_boleto: str) -> dict:
    """Calcula o valor com desconto caso o boleto seja pago antes do vencimento."""
    boletos = _carregar_boletos()
    clientes = _carregar_clientes()

    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}
    
    b = boleto.iloc[0]
    if b["status"] != "Pendente":
        return {
            "encontrado": True,
            "elegivel": False,
            "mensagem": f"O boleto {id_boleto} está com status '{b['status']}' e não é elegível para desconto por antecipação.",
        }
    
    cliente = clientes[clientes["cpf"] == b["cpf_cliente"]].iloc[0]
    desconto_pct = float(cliente["desconto_pagamento_antecipado_pct"])
    valor_original = float(b["valor"])
    valor_com_desconto = round(valor_original * (1 - desconto_pct / 100), 2)
    dias_para_vncer = (b["data_vencimento"] - HOJE).days

    return {
        "encontrado": True,
        "elegivel": dias_para_vncer > 0,
        "id_boleto": id_boleto,
        "valor_original": valor_original,
        "desconto_pct": desconto_pct,
        "valor_com_desconto": valor_com_desconto,
        "economia": round(valor_original - valor_com_desconto, 2),
        "dias_para_vencer": dias_para_vncer
    }

def verificar_credito(cpf: str) -> dict:
    """Verifica o limite de crédito, valor utilizado, disponivel e status do cliente."""
    cliente = identificar_cliente_por_cpf(cpf)
    if not cliente["encontrado"]:
        return cliente
    
    limite = float(cliente["limite_credito"])
    usado = float(cliente["credito_utilizado"])
    disponivel = round(limite - usado, 2)
    percentual_uso = round((usado / limite) * 100, 1) if limite else 0

    return {
        "encontrado": True,
        "cliente": cliente["nome"],
        "status_credito": cliente["status_credito"],
        "limite_credito": limite,
        "credito_utilizado": usado,
        "credito_disponivel": disponivel,
        "percentual_utilizado": percentual_uso,
    }

#emisao segunda via do boleto
def emitir_segunda_via_boleto(id_boleto: str) -> dict:
    """Gera os dados para emissão da 2º via de um boleto."""
    boletos = _carregar_boletos()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}
    
    b = boleto.iloc[0]
    if b["status"] == "Pago":
        return {"encontrado": True, "emitido": False, "mensagem": f"O boleto {id_boleto} já está pago, não é possivel emitir 2ª via."}
    
    return {
        "encontrado": True,
        "emitido": True,
        "id_boleto": id_boleto,
        "valor": float(b["valor"]),
        "linha_digitavel": b["linha_digitavel"],
        "mensagem": f"2ª via do boleto {id_boleto} emitida com suceso."
    }

#Alterar forma de pagamento
def _salvar_boletos(df: pd.DataFrame):
    df.to_csv(BOLETOS_PATH, index=False)

FORMAS_VALIDAS = ["Boleto", "PIX", "Cartão de Crédito", "Transferência (TED)"]

def alterar_forma_pagamento(id_boleto: str, nova_forma: str) -> dict:
    """Altera a forma de pagamento de um boleto (ex.: de Boleto para PIX)."""
    if nova_forma not in FORMAS_VALIDAS:
        return {"Sucesso": False, "mensagem": f"Forma de pagamento inválida. Opções: {', '.join(FORMAS_VALIDAS)}."}
    
    boletos = _carregar_boletos()
    idx = boletos.index[boletos["id_boleto"] == id_boleto]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} não encontrado."}
    
    boletos.loc[idx, "forma_pagamento"] = nova_forma
    _salvar_boletos(boletos)
    return {"sucesso": True, "mensagem": f"Forma de pagamento do boleto {id_boleto} alterada para {nova_forma}."}


#alterar data de vencimento
def alterar_data_vencimento(id_boleto: str, nova_data: str) -> dict:
    """Altera a data de vencimento de um boleto. nova_data no formato AAAA-MM-DD."""
    try:
        nova_data_dt = datetime.strptime(nova_data, "%Y-%m-%d").date()
    except ValueError:
        return {"sucesso": False, "mensagem": "Data inválida. Use o formato AAAA-MM-DD."}  

    boletos = _carregar_boletos()
    idx = boletos.index[boletos["id_boleto"] == id_boleto]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"Boleto {id_boleto} não encontrado."}  
    
    boletos.loc[idx, "data_vencimento"] = nova_data_dt
    if (boletos.loc[idx, "status"] == "Vencido").any():
        boletos.loc[idx, "status"] = "Pendente"
    _salvar_boletos(boletos)
    return {"sucesso": True, "mensagem": f"Vencimento do boleto {id_boleto} alterado para {nova_data}. "}

#Gerar relatorio de cobrança
def gerar_relatorio_cobranca(cpf: str) -> dict:
    """Gera um resumo de cobrança consolidado de um cliente: crédito, vencidos e pendentes."""
    credito = verificar_credito(cpf)
    if not credito.get("encontrado"):
        return credito
    
    vencimentos = analisar_vencimento_boletos(cpf)

    return {
        "encontrado": True,
        "cliente": credito["cliente"],
        "status_credito": credito.get("status_credito"),
        "credito_disponivel": credito["credito_disponivel"],
        "total_vencidos": vencimentos["total_vencidos"],
        "boletos_vencidos": vencimentos["boletos_vencidos"],
        "total_pendentes": vencimentos["total_pendentes"],
        "boletos_pendentes": vencimentos["boletos_pendentes"],
    }

#Calcular juros / Multas por atraso
TAXA_MULTA_ATRASO_PCT = 2.0 #multa fixa por atraso
TAXA_JUROS_DIARIO_PCT = 0.033 # juros de mora -1%/mes

def calcular_juros_multa_atraso(id_boleto: str) -> dict:
    """Calcula multa e juros de mora acumulados de um boleto vencido e não pago,
    retornando o valor atualizado a pagar hoje."""
    boletos = _carregar_boletos()
    boleto = boletos[boletos["id_boleto"] == id_boleto]
    if boleto.empty:
        return {"encontrado": False, "mensagem": f"Boleto {id_boleto} não encontrado."}
    
    b = boleto.iloc[0]
    if b["status"] != "Vencido":
        return {
            "encontrado": True,
            "aplica_encargos": False,
            "mensagem": f"O boleto {id_boleto} está com status '{b['status']}', não há encargos de atraso a calcular.",
        }
    
    dias_atraso = (HOJE - b["data_vencimento"]).days
    valor_original = float(b["valor"])
    multa = round(valor_original * (TAXA_MULTA_ATRASO_PCT / 100), 2)
    juros = round(valor_original * (TAXA_JUROS_DIARIO_PCT / 100) * dias_atraso, 2)
    valor_atualizado = round(valor_original + multa + juros, 2)

    return {
        "encontrado": True,
        "aplica_encargos": True,
        "id_boleto": id_boleto,
        "dias_atraso": dias_atraso,
        "valor_original": valor_original,
        "valor_multa": multa,
        "valor_juros": juros,
        "valor_atualizado": valor_atualizado,
    }


#Consultar historico de pagamento
def consultar_historico_pagamento(cpf: str) -> dict:
    """Analisa o histórico de boletos do cliente (pagos em dia, pagos com
    atraso, vencidos em aberto) e calcula um score simples de pagador."""
    boletos = _carregar_boletos()
    do_cliente = boletos[boletos["cpf_cliente"] == cpf].copy()
    if do_cliente.empty:
        return {"encontrado": False, "mensagem": f"Nenhum boleto encontrado para o CPF {cpf}. "}
    
    pagos = do_cliente[do_cliente["status"] == "Pago"].copy()
    pagos["data_pagamento_dt"] = pd.to_datetime(pagos["data_pagamento"]).dt.date
    pagos_em_dia = pagos[pagos["data_pagamento_dt"] <= pagos["data_vencimento"]]
    pagos_com_atraso = pagos[pagos["data_pagamento_dt"] > pagos["data_vencimento"]]
    vencidos_em_aberto = do_cliente[do_cliente["status"] == "Vencido"]

    pct_pontualidade = round(len(pagos_em_dia)/ len(pagos) * 100, 1) if len(pagos) else None

    if len(vencidos_em_aberto) >= 3 or (pct_pontualidade is not None and pct_pontualidade < 50):
        score = "Inadimplente contumaz"
    elif len(vencidos_em_aberto) >= 1 or (pct_pontualidade is not None and pct_pontualidade < 80):
        score = "Atraso recorrente"
    else:
        score = "Bom pagador"

    return {
        "encontrado": True,
        "pagos_em_dia": len(pagos_em_dia),
        "pagos_com_atraso": len(pagos_com_atraso),
        "vencidos_em_aberto": len(vencidos_em_aberto),
        "percentual_pontualidade": pct_pontualidade,
        "score_pagador": score,
    }
     
    # verificar restriçao de credito
def verificar_restricao_credito(cpf: str) -> dict:
        """Consulta se o cliente possui restrição registrada em órgãos de
    proteção ao crédito (SPC/Serasa) — dado cadastral simulado."""
        cliente = identificar_cliente_por_cpf(cpf)
        if not cliente["encontrado"]:
            return cliente
        
        possui_restricao = cliente["restricao_spc_serasa"] == "Sim"

        return {
            "encontrado": True,
            "cliente": cliente["nome"],
            "possui_restricao": possui_restricao,
            "mensagem": (
                f"O CPF {cpf} possui restrição ativa em SPC/Serasa."
                if possui_restricao
                else f"O CPF {cpf} não possui restrição em SPC/Serasa no momento."
            ),
        }

# bloquear e desbloquear pedidos
def _salvar_clientes(df: pd.DataFrame):
    df.to_csv(CLIENTES_PATH, index=False)

def bloquear_desbloquear_pedidos(cpf: str, acao: str) -> dict:
    """Bloqueia ou libera a realização de novos pedidos para um cliente.
    acao deve ser 'bloquear' ou 'desbloquear'."""
    if acao not in {"bloquear", "desbloquear"}:
        return {"sucesso": False, "mensagem": "Ação inválida. Use 'bloquear' ou 'desbloquear'."}
    
    clientes = _carregar_clientes()
    idx = clientes.index[clientes["cpf"] == cpf]
    if len(idx) == 0:
        return {"sucesso": False, "mensagem": f"Cliente com CPF {cpf} não encontrado."}
    
    novo_valor = "Sim" if acao == "bloquear" else "Não"
    clientes.loc[idx, "pedidos_bloqueados"] = novo_valor
    _salvar_clientes(clientes)

    verbo = "bloqueados" if acao == "bloquear" else "liberados"
    return {"sucesso": True, "mensagem": f"Novos perdidos do CPF {cpf} foram {verbo} com sucesso."}

#negociar parcelamento de dividas
def negociar_parcelamento_divida(cpf: str, numero_parcelas: int) -> dict:
    """Consolida todos os boletos vencidos em aberto de um cliente em um
    novo parcelamento, gerando novos boletos mensais."""
    if numero_parcelas < 1 or numero_parcelas > 12:
        return {"sucesso": False, "mensagem": "Número de parcelas deve ser entre 1 e 12."}

    boletos = _carregar_boletos()
    vencidos_idx = boletos.index[(boletos["cpf_cliente"] == cpf) & (boletos["status"] == "Vencido")]
    if len(vencidos_idx) == 0:
        return {"sucesso": False, "mensagem": f"Nenhum boleto vencido em aberto encontrado para o CPF {cpf}."}

    valor_total = float(boletos.loc[vencidos_idx, "valor"].sum())
    valor_total_atualizado = round(valor_total * (1 + TAXA_MULTA_ATRASO_PCT / 100), 2)
    valor_parcela = round(valor_total_atualizado / numero_parcelas, 2)

    boletos.loc[vencidos_idx, "status"] = "Renegociado"

    max_id = boletos["id_boleto"].str.extract(r"(\d+)").astype(int).max().iloc[0]
    novas_linhas = []
    for p in range(1, numero_parcelas + 1):
        max_id += 1
        novas_linhas.append({
            "id_boleto": f"BOL-{max_id:05d}",
            "cpf_cliente": cpf,
            "descricao": f"Parcela {p}/{numero_parcelas} - renegociação de dívida",
            "valor": valor_parcela,
            "data_emissao": HOJE.isoformat(),
            "data_vencimento": (HOJE + timedelta(days=30 * p)).isoformat(),
            "status": "Pendente",
            "forma_pagamento": "Boleto",
            "linha_digitavel": " ".join(str(random.randint(10000, 99999)) for _ in range(5)),
            "data_pagamento": "",
        })

    boletos = pd.concat([boletos, pd.DataFrame(novas_linhas)], ignore_index=True)
    _salvar_boletos(boletos)

    return {
        "sucesso": True,
        "valor_original_vencido": round(valor_total, 2),
        "valor_total_atualizado": valor_total_atualizado,
        "numero_parcelas": numero_parcelas,
        "valor_por_parcela": valor_parcela,
        "novos_boletos": [n["id_boleto"] for n in novas_linhas],
        "mensagem": (
            f"Dívida de R$ {valor_total:.2f} renegociada em {numero_parcelas}x de "
            f"R$ {valor_parcela:.2f}. Novos boletos: {', '.join(n['id_boleto'] for n in novas_linhas)}."
        ),
    }

    #Abrri chamado de contestacao
CHAMADOS_PATHS = os.path.join(BASE_DIR, "data", "chamados.csv")

def _carregar_chamados() -> pd.DataFrame:
    if not os.path.exists(CHAMADOS_PATHS):
            return pd.DataFrame(columns=["id_chamado", "cpf_cliente", "id_boleto", "motivo", "data_abertura", "status"])
    return pd.read_csv(CHAMADOS_PATHS, dtype=str)

def _salvar_chamados(df: pd.DataFrame):
    df.to_csv(CHAMADOS_PATHS, index=False)

def abrir_chamado_contestacao(cpf: str, id_boleto: str, motivo: str) -> dict:
     """Abre um chamado interno de contestação/dúvida sobre uma cobrança
    específica, para análise do time financeiro."""
     chamados = _carregar_chamados()
     novo_id = f"CHM-{len(chamados) + 1:05d}"
     novo = {
         "id_chamado": novo_id,
        "cpf_cliente": cpf,
        "id_boleto": id_boleto,
        "motivo": motivo,
        "data_abertura": HOJE.isoformat(),
        "status": "Aberto",
    }

     chamados = pd.concat([chamados, pd.DataFrame([novo])], ignore_index=True)
     _salvar_chamados(chamados)

     return {
         "sucesso": True,
        "id_chamado": novo_id,
        "mensagem": f"Chamado {novo_id} aberto com sucesso para o boleto {id_boleto}. O time financeiro irá analisar.",
     } 

#Gerar relatorio de inadimplencia geral
def gerar_relatorio_inadimplencia_geral() -> dict:
    """Gera um relatório gerencial consolidado de inadimplência de toda a
    carteira de clientes, com faixas de atraso (aging) e total em aberto."""
    boletos = _carregar_boletos()
    vencidos = boletos[boletos["status"] == "Vencido"].copy()
    if vencidos.empty:
        return {"total_vencido": 0, "quantidade_boletos_vencidos": 0, "mensagem": "Nenhum boleto vencido na carteira." }
    
    vencidos["dias_atraso"] = vencidos["data_vencimento"].apply(lambda d: (HOJE - d ).days)

    def faixa(dias):
        if dias <= 30:
            return "0-30 dias"
        elif dias <= 60:
            return "31-60 dias"
        elif dias <= 90:
            return "61-90 dias"
        return "90+ dias"
    
    vencidos["faixa_aging"] = vencidos["dias_atraso"].apply(faixa)
    aging = vencidos.groupby("faixa_aging")["valor"].agg(["count", "sum"]). round(2)

    aging_dict = {
        faixa: {"quantidade": int(row["count"]), "valor_total": float(row["sum"])}
        for faixa, row in aging.iterrows()
    }

    clientes_inadimplentes = vencidos["cpf_cliente"].nunique()

    return {
        "total_vencido": round(float(vencidos["valor"].sum()), 2),
        "quantidade_boletos_vencidos": len(vencidos),
        "clientes_inadimplentes": int(clientes_inadimplentes),
        "aging": aging_dict,
    }