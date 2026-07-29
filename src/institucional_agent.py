import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .institucional_data import CONTEUDO_EMPRESA

load_dotenv()

MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT_INSTITUCIONAL = f"""\
Você é o Assistente Institucional da PetroMax Química, uma empresa do \
setor petroquímico. Seu papel é responder dúvidas de clientes e visitantes \
sobre a empresa, produtos, entregas, segurança e certificações.

Use SOMENTE as informações abaixo para responder. Se a pergunta não puder \
ser respondida com essas informações, diga educadamente que não tem esse \
dado e sugira contato com a equipe comercial.

{CONTEUDO_EMPRESA}

Responda sempre em português, de forma amigável e objetiva.
"""


def build_institucional_agent():
    """Constrói uma chain simples (LLM + prompt), sem tools."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não encontrada no .env.")

    llm = ChatGroq(model=MODEL_NAME, temperature=0.3, api_key=api_key)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_INSTITUCIONAL),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
    ])

    return prompt | llm