"""
Aplicação web (FastAPI)
"""

from fastapi import FastAPI
from pydantic import BaseModel

from src.agent import build_agent

app = FastAPI(title="Agente PetroMax Química")

_agent_executor = None
_sessoes: dict[str, list] = {}

def get_agent():
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = build_agent()
    return _agent_executor

class Pergunta(BaseModel):
    session_id: str = "default"
    mensagem: str

@app.post("/perguntar")
def perguntar(p: Pergunta):
    agent_executor = get_agent()
    historico = _sessoes.setdefault(p.session_id, [])

    resultado = agent_executor.invoke({"input": p.mensagem, "chat_history": historico})
    texto = resultado["output"]

    historico.append(("human", p.mensagem))
    historico.append(("ai", texto))
    return {"resposta": texto}

@app.get("/health")
def health():
    return {"status": "ok"}