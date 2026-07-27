"""
Gera dados fictícios de clientes e belotos para o agente da PetroMAX Quimica.
Exetutar um unica vez para (re)criar os csvs em data/.

"""

import csv
import random
from datetime import date, timedelta

random.seed(42)

HOJE = date(2026, 7, 26) # data referencia do projeto

NOMES = [
    "Carlos Eduardo Ferreira", "Mariana Souza Lima", "João Batista Nogueira", 
    "Fernanda Ribeiro Castro", "Roberto Almeida Pinto", "Juliana Martins Rocha",
    "Antônio Carlos Vieira", "Patrícia Gomes Andrade", "Ricardo Tavares Neto",
    "Camila Duarte Barros", "Sérgio Henrique Melo", "Renata Costa Farias",
    "Eduardo Lopes Cardoso", "Vanessa Cristina Reis", "Marcelo Aguiar Teixeira",
]

EMPRESAS = [
    "Posto Rota Sul Ltda", "Distribuidora Alfa Combustíveis", "Química Bela Vista ME",
    "Transportes Nogueira & Cia", "Indústria Vale Verde S.A.", "Comercial Ferreira EPP",
    "Auto Posto Pinheiros", "Grupo Andrade Petroquímicos", "Lubrificantes Sul Ltda",
    "Distribuidora Central de Combustíveis", "Resinas & Polímeros Barros",
    "Petro Comércio Reis", "Química Industrial Teixeira", "Posto Cardoso & Filhos",
    "Solventes Melo Distribuição",
]

STATUS_CREDITO = ["Aprovado", "Aprovado", "Aprovado", "Análise", "Restrito"]
FORMAS_PAGAMENTO = ["Boleto", "PIX", "Cartão de Crédito", "Transferência (TED)"]

def gerar_cpf():
    n = [random.randint(0, 9) for _ in range(9)]

    def dv(nums, peso_inicial):
        s = sum(n * p for n, p in zip(nums, range(peso_inicial, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    
    d1 = dv(n, 10)
    d2 = dv(n + [d1], 11)
    n += [d1, d2]
    return f"{n[0]}{n[1]}{n[2]}.{n[3]}{n[4]}{n[5]}.{n[6]}{n[7]}{n[8]}-{n[9]}{n[10]}"

def gerar_clientes(qtd=15):
    clientes = []
    for i in range(qtd):
        limite = random.choice([5000, 8000, 10000, 15000, 20000, 30000, 50000])
        usado = round(limite * random.uniform(0.1, 0.95), 2)
        cpf = gerar_cpf()
        status_credito = random.choice(STATUS_CREDITO)
        clientes.append({
            "cpf": cpf,
            "nome": NOMES[i],
            "empresa": EMPRESAS[i],
            "telefone": f"(11) 9{random.randint(6000,9999)}-{random.randint(1000,9999)}",
            "email": NOMES[i].lower().split()[0] + "." + NOMES[i].lower().split()[-1] + "@" + EMPRESAS[i].lower().split()[0].replace("ã","a").replace("ç","c") + ".com.br",
            "limite_credito": limite,
            "credito_utilizado": usado,
            "status_credito": status_credito,
            "desconto_pagamento_antecipado_pct": random.choice([3, 5, 8, 10]),
            "pedidos_bloqueados": "Sim" if status_credito == "Restrito" else "Não",
            "restricao_spc_serasa": "Sim" if status_credito == "Restrito" and random.random() < 0.5 else "Não",
        })
    return clientes


def gerar_boletos(clientes, qtd_por_cliente=(2, 5)):
    boletos = []
    id_seq = 1
    for c in clientes:
        n_boletos = random.randint(*qtd_por_cliente)
        for _ in range(n_boletos):
            dias_emissao = random.randint(-90, 10)
            data_emissao = HOJE + timedelta(days=dias_emissao)
            prazo = random.choice([15, 21, 28, 30])
            data_vencimento = data_emissao + timedelta(days=prazo)
            valor = round(random.uniform(800, 25000), 2)

            if data_vencimento < HOJE:
                status = random.choices(["Vencido", "Pago"], weights=[0.55, 0.45])[0]
            elif data_vencimento <= HOJE + timedelta(days=7):
                status = random.choices(["Pendente", "Pago"], weights=[0.7, 0.3])[0]
            else:
                status = "Pendente"

            data_pagamento = ""
            if status == "Pago":
                atraso_pagto = random.randint(-5, 3)
                data_pagamento = (data_vencimento + timedelta(days=atraso_pagto)).isoformat()

            boletos.append({
                "id_boleto": f"BOL-{id_seq:05d}",
                "cpf_cliente": c["cpf"],
                "descricao": random.choice([
                "Fornecimento de nafta petroquimica",
                "Venda de resinas plásticas",
                "Fornecimento de solventes industriais",
                "Venda de lubrificantes automotivos",
                "Fornecimento de combustível a granel",
                "Venda de polímeros técnicos",
            ]),

                "valor": valor,
                "data_emissao": data_emissao.isoformat(),
                "data_vencimento": data_vencimento.isoformat(),
                "status": status,
                "forma_pagamento": random.choice(FORMAS_PAGAMENTO),
                "linha_digitavel": " ".join(str(random.randint(10000, 99999)) for _ in range(5)),
                "data_pagamento": data_pagamento,
            })
            id_seq += 1
    return boletos

def salvar_csv(caminho, dados, campos):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(dados)

if __name__ == "__main__":
    clientes = gerar_clientes()
    boletos = gerar_boletos(clientes)

    salvar_csv(
        "data/clientes.csv",
        clientes,
        ["cpf", "nome", "empresa", "telefone", "email", "limite_credito", "credito_utilizado", 
         "status_credito", "desconto_pagamento_antecipado_pct", "pedidos_bloqueados", "restricao_spc_serasa"],
    )

    salvar_csv(
        "data/boletos.csv",
        boletos,
        ["id_boleto", "cpf_cliente", "descricao", "valor", "data_emissao", "data_vencimento", "status", "forma_pagamento",
         "linha_digitavel", "data_pagamento"],
    )

    with open("data/chamados.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id_chamado", "cpf_cliente", "id_boleto", "motivo", "data_abertura", "status"
        ])
        writer.writeheader()

    print(f"{len(clientes)} clientes e {len(boletos)} boletos gerados em data/")