import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from src.agent import TOOLS, SYSTEM_PROMPT

load_dotenv()

llm = ChatOpenAI(
    model="openrouter/free",
    temperature=0,
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, TOOLS, prompt)
agente_or = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)

resposta = agente_or.invoke({
    "input": "Parcele a dívida vencida do CPF 351.161.559-35 em 3 vezes"
})
print(resposta["output"])