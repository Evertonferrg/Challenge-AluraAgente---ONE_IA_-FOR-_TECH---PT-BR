"""
agent.py
Monta o agente de IA (LangChain + Groq) que orquestra as ferramentas de 
credito e cobrança da PetroMax Quimica.
"""
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from . import tools as biz

load_dotenv()

MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile") 

@tool
def verificar_credito(cpf: str) -> dict:
    """
    Verifica o limite de crédito, valor utilizado e disponível de um 
    cliente pelo CPF.
    """
    return biz.verificar_credito(cpf)
@tool
def identificar_cliente_por_cpf(cpf: str) -> dict:
    """Identifica um cliente da PetroMax Quimica a partir do CPF informamado,
    retornando nome, empresa, contato e status de crédito.
    """
    return biz.identificar_cliente_por_cpf(cpf)

@tool
def analisar_vencimento_boletos(cpf: str) -> dict:
    """Lista todos os boletos pendentes e vencidos de um cliente, com dias
    para vencer ou dias em atraso.
    """
    return biz.analisar_vencimento_boletos(cpf)

@tool
def verificar_notas_vencidas(cpf: str) -> dict:
    """Retorna somente as notas/boletos vencidos e não pagos de um cliente, 
    incluindo o valor total em atraso. Útil para ações de cobrança.
    """
    return biz.verificar_notas_vencidas(cpf)

@tool
def verificar_desconto_pagamento_antecipado(id_boleto: str) -> dict:
    """Calcula o valor com desconto para pagamento antecipado de um boleto
    específico, informando o percentual de desconto e a economia."""
    return biz.verificar_desconto_pagamento_antecipado(id_boleto)


@tool
def emitir_segunda_via_boleto(id_boleto: str) -> dict:
    """Emite a 2ª via de um boleto (para boletos pendentes ou vencidos),
    retornando linha digitável e valor."""
    return biz.emitir_segunda_via_boleto(id_boleto)


@tool
def enviar_segunda_via_por_email(id_boleto: str, email: str = None) -> dict:
    """Emite a 2ª via de um boleto e ENVIA POR E-MAIL ao cliente (usa o
    e-mail cadastrado do cliente, ou um e-mail alternativo se informado)."""
    return biz.enviar_segunda_via_por_email(id_boleto, email)


@tool
def alterar_forma_pagamento(id_boleto: str, nova_forma: str) -> dict:
    """Altera a forma de pagamento de um boleto. Valores aceitos: 'Boleto',
    'PIX', 'Cartão de Crédito', 'Transferência (TED)'."""
    return biz.alterar_forma_pagamento(id_boleto, nova_forma)


@tool
def alterar_data_vencimento(id_boleto: str, nova_data: str) -> dict:
    """Altera a data de vencimento de um boleto. A nova_data deve estar no
    formato AAAA-MM-DD."""
    return biz.alterar_data_vencimento(id_boleto, nova_data)


@tool
def enviar_comprovante_pagamento(id_boleto: str, email: str = None) -> dict:
    """Envia o comprovante de pagamento de um boleto já pago para o e-mail
    do cliente ou para um e-mail informado."""
    return biz.enviar_comprovante_pagamento(id_boleto, email)


@tool
def gerar_relatorio_cobranca(cpf: str) -> dict:
    """Gera um relatório consolidado de cobrança de um cliente: crédito
    disponível, boletos vencidos e boletos pendentes."""
    return biz.gerar_relatorio_cobranca(cpf)


@tool
def calcular_juros_multa_atraso(id_boleto: str) -> dict:
    """Calcula multa e juros de mora acumulados de um boleto vencido,
    retornando o valor atualizado a ser pago hoje."""
    return biz.calcular_juros_multa_atraso(id_boleto)


@tool
def consultar_historico_pagamento(cpf: str) -> dict:
    """Consulta o histórico de pagamentos de um cliente e calcula seu score
    de pagador: 'Bom pagador', 'Atraso recorrente' ou 'Inadimplente contumaz'."""
    return biz.consultar_historico_pagamento(cpf)


@tool
def verificar_restricao_credito(cpf: str) -> dict:
    """Verifica se o cliente possui restrição registrada em órgãos de
    proteção ao crédito (SPC/Serasa)."""
    return biz.verificar_restricao_credito(cpf)


@tool
def bloquear_desbloquear_pedidos(cpf: str, acao: str) -> dict:
    """Bloqueia ou libera novos pedidos de um cliente por inadimplência.
    acao deve ser 'bloquear' ou 'desbloquear'."""
    return biz.bloquear_desbloquear_pedidos(cpf, acao)


@tool
def negociar_parcelamento_divida(cpf: str, numero_parcelas: int) -> dict:
    """Renegocia/parcela toda a dívida vencida em aberto de um cliente em
    um número de parcelas (1 a 12), gerando novos boletos mensais."""
    return biz.negociar_parcelamento_divida(cpf, numero_parcelas)


@tool
def enviar_alerta_vencimento_proximo(cpf: str, dias_antecedencia: int = 3) -> dict:
    """Envia por e-mail um alerta preventivo de boletos que vencem nos
    próximos N dias (régua de cobrança, padrão 3 dias)."""
    return biz.enviar_alerta_vencimento_proximo(cpf, dias_antecedencia)


@tool
def abrir_chamado_contestacao(cpf: str, id_boleto: str, motivo: str) -> dict:
    """Abre um chamado interno de contestação sobre uma cobrança que o
    cliente considera indevida ou tem dúvidas, para análise do financeiro."""
    return biz.abrir_chamado_contestacao(cpf, id_boleto, motivo)


@tool
def gerar_relatorio_inadimplencia_geral() -> dict:
    """Gera um relatório gerencial de inadimplência de toda a carteira de
    clientes, com faixas de atraso (aging: 0-30, 31-60, 61-90, 90+ dias)."""
    return biz.gerar_relatorio_inadimplencia_geral()

TOOLS = [
    identificar_cliente_por_cpf,
    verificar_credito,
    analisar_vencimento_boletos,
    verificar_notas_vencidas,
    verificar_desconto_pagamento_antecipado,
    emitir_segunda_via_boleto,
    enviar_segunda_via_por_email,
    alterar_forma_pagamento,
    alterar_data_vencimento,
    enviar_comprovante_pagamento,
    gerar_relatorio_cobranca,
    calcular_juros_multa_atraso,
    consultar_historico_pagamento,
    verificar_restricao_credito,
    bloquear_desbloquear_pedidos,
    negociar_parcelamento_divida,
    enviar_alerta_vencimento_proximo,
    abrir_chamado_contestacao,
    gerar_relatorio_inadimplencia_geral,
]

SYSTEM_PROMPT = """\
Você é o Agente PetroMax, assistente virtual de crédito e cobrança da \
PetroMax Química, uma empresa do setor petroquímico.

Seu papel é ajudar colaboradores(as) do time financeiro e de atendimento a:
- identificar clientes pelo CPF;
- consultar e analisar crédito disponível;
- verificar boletos pendentes, vencidos e próximos do vencimento;
- calcular descontos por pagamento antecipado e juros/multa de atraso;
- emitir 2ª via de boletos e enviá-la por e-mail;
- alterar forma de pagamento e data de vencimento;
- enviar comprovantes de pagamento e alertas de vencimento por e-mail;
- consultar histórico e score de pagamento, e restrição em SPC/Serasa;
- bloquear/liberar novos pedidos e negociar parcelamento de dívidas;
- abrir chamados de contestação de cobrança;
- gerar relatórios de cobrança e de inadimplência da carteira.

Regras:
1. Sempre que a pergunta envolver um cliente específico, peça o CPF caso \
não tenha sido informado.
2. Use as ferramentas disponíveis para buscar dados reais — nunca invente \
valores, datas ou status.
3. Responda sempre em português, de forma clara e profissional.
4. Ao apresentar valores monetários, use o formato R$ 0.000,00.
"""

def build_agent() -> AgentExecutor:
    """Constrói e retorna o AgentExecutor pronto para uso. """
    # api_key = os.getenv("GROQ_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY não encontrada no .env.")
        llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free"),
            temperature=0,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY não encontrada no .env.")
        llm = ChatGroq(model=MODEL_NAME, temperature=0, api_key=api_key)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=False)

@tool
def gerar_relatorio_inadimplencia_geral(motivo_consulta: str = "geral") -> dict:
    """Gera um relatório gerencial de inadimplência de toda a carteira de
    clientes, com faixas de atraso (aging: 0-30, 31-60, 61-90, 90+ dias).
    O parâmetro motivo_consulta pode ser preenchido com qualquer texto ou
    deixado no padrão."""
    return biz.gerar_relatorio_inadimplencia_geral()

