"""
Aplicação web (FastAPI)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from src.institucional_agent import build_institucional_agent

from src.agent import build_agent

app = FastAPI(title="Agente PetroMax Química")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

app.mount("/", StaticFiles(directory="petromax-frontend/dist", html=True), name="site")

_institucional_chain = None
_sessoes_institucional: dict[str, list] = {}


def get_institucional_chain():
    global _institucional_chain
    if _institucional_chain is None:
        _institucional_chain = build_institucional_agent()
    return _institucional_chain


@app.post("/perguntar-institucional")
def perguntar_institucional(p: Pergunta):
    chain = get_institucional_chain()
    historico = _sessoes_institucional.setdefault(p.session_id, [])

    resultado = chain.invoke({"input": p.mensagem, "chat_history": historico})
    texto = resultado.content

    historico.append(("human", p.mensagem))
    historico.append(("ai", texto))
    return {"resposta": texto}