import pandas as pd
import os 
from datetime import date
from datetime import date, datetime, timedelta

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

# verificação de credito

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
        "limite_credito": limite,
        "credito_utilizado": usado,
        "credito_disponivel": disponivel,
        "percentual_utilizado": percentual_uso,
    }

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