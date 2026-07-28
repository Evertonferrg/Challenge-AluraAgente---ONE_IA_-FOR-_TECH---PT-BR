# from src.agent import build_agent

# agente = build_agent()

# perguntas = [
#     ("18. abrir_chamado_contestacao", "Abra um chamado de contestação para o CPF 433.218.196-43 sobre o boleto BOL-00001, motivo: cliente alega já ter pago"),
#     ("19. negociar_parcelamento_divida", "Parcele a dívida vencida do CPF 351.161.559-35 em 3 vezes"),
# ]

# for numero, pergunta in perguntas:
#     print(f"\n{'='*70}\n{numero}\nPergunta: {pergunta}\n{'-'*70}")
#     resposta = agente.invoke({"input": pergunta})
#     print(f"Resposta: {resposta['output']}")

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

chave = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=chave,
    transport="rest",   # ← força REST em vez de gRPC
)
resposta = llm.invoke("Diga só a palavra 'funcionou'.")
print(resposta.content)