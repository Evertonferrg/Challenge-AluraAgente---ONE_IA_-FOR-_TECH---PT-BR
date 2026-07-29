from src.institucional_agent import build_institucional_agent

chain = build_institucional_agent()
resposta = chain.invoke({"input": "Vocês entregam em todo o Brasil?", "chat_history": []})
print(resposta.content)