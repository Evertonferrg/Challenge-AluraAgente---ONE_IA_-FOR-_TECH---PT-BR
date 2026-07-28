"""
main.py
Interface de linha de comando (CLI) para conversar com o Agente PetroMax
diretamente no terminal, sem precisar editar um script a cada pergunta.

Uso:
    python -m src.main
"""

from src.agent import build_agent

def main():
    print("=" * 60)
    print(" Agente PetroMax Quimica - Crédito e Cobrança")
    print("=" * 60)
    print("Digite sua pergunta (ou 'sair' para encerrar).\n")

    agent_executor = build_agent()
    historico = []

    while True:
        pergunta = input("Você: ").strip()
        if pergunta.lower() in {"sair", "exit", "quit"}:
            print("Até logo!")
            break
        if not pergunta:
            continue

        resposta = agent_executor.invoke({"input": pergunta, "chat_history": historico})
        texto = resposta["output"]
        print(f"\nAgente: {texto}\n")

        historico.append(("human", pergunta))
        historico.append(("ai", texto))

if __name__ == "__main__":
    main()
