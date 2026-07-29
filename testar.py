
"""
Teste local do Agente PetroMax.
 
AJUSTE O IMPORT ABAIXO para o caminho real do seu módulo
(ex.: from src.agent import responder)
"""
 
from src.agent import responder  # <-- TODO: corrija esse caminho se necessário
 
 
def linha(titulo):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)
 
 
# ---------------------------------------------------------------------------
# 1) Perguntas institucionais -> devem responder direto, SEM pedir cadastro
# ---------------------------------------------------------------------------
# linha("1) Institucional - história/fundação")
# print(responder("Qual a história e quem fundou a PetroMax?", session_id="sess_1"))
#
# linha("2) Institucional - produtos")
# print(responder("Quais produtos vocês vendem?", session_id="sess_2"))
#
# linha("3) Institucional - horário de funcionamento")
# print(responder("Qual o horário de funcionamento da empresa?", session_id="sess_3"))
#
# linha("4) Institucional - quantidade de funcionários")
# print(responder("Quantos funcionários vocês têm?", session_id="sess_4"))
 
 
# ---------------------------------------------------------------------------
# 2) Pergunta comercial SEM autenticação -> deve pedir nome + matrícula
#    (não deve chamar nenhuma tool de crédito/cobrança)
# ---------------------------------------------------------------------------
# linha("5) Comercial SEM login -> espera pedido de cadastro")
# print(responder("Qual o crédito disponível do CPF 123.456.789-00?", session_id="sess_5"))
 
 
# ---------------------------------------------------------------------------
# 3) Pergunta comercial com credenciais ERRADAS -> deve recusar
# ---------------------------------------------------------------------------
# linha("6) Comercial com credencial INVÁLIDA -> espera recusa")
# print(responder(
#     "Qual o crédito disponível do CPF 123.456.789-00?",
#     session_id="sess_6",
#     nome="Fulano Inexistente",
#     matricula="0000",
# ))
 
 
# ---------------------------------------------------------------------------
# 4) Pergunta comercial com credenciais VÁLIDAS -> deve autenticar e
#    seguir para o agente/tools
#    TODO: troque NOME_VALIDO e MATRICULA_VALIDA por um registro real
#    do seu data/funcionarios.csv
# ---------------------------------------------------------------------------
NOME_VALIDO = "Marina Costa Alves"
MATRICULA_VALIDA = "00002@1"
 
linha("7) Comercial com credencial VÁLIDA -> autentica e consulta")
print(responder(
    "Qual o crédito disponível do CPF 433.218.196-43?",
    session_id="sess_7",
    nome=NOME_VALIDO,
    matricula=MATRICULA_VALIDA,
))
 
 
# ---------------------------------------------------------------------------
# 5) Mesma sessão já autenticada -> NÃO deve pedir cadastro de novo
# ---------------------------------------------------------------------------
linha("8) Mesma sessão (sess_7) já autenticada -> segue direto")
print(responder(
    "Quais são os boletos vencidos do CPF 433.218.196-43?",
    session_id="sess_7",
))
 
 
# ---------------------------------------------------------------------------
# 6) Envio da 2ª via do boleto por e-mail
# ---------------------------------------------------------------------------
linha("9) Enviar 2ª via do boleto BOL-00001 por e-mail")
print(responder(
    "Envie a 2ª via do boleto BOL-00001 para o e-mail ferreiraguedeseverton@gmail.com",
    session_id="sess_7",
))
 