import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

import pandas as pd

from . import tools as biz



MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ---------------------------------------------------------------------------
# Cadastro de funcionarios (autenticacao por sessao)
# ---------------------------------------------------------------------------
df_funcionarios = pd.read_csv("data/funcionarios.csv")

# guarda em memoria quais sessoes ja foram autenticadas
sessao_funcionario = {}


def validar_funcionario(nome: str, matricula: str) -> bool:
    """Confere se nome + matricula batem com o cadastro."""
    resultado = df_funcionarios[
        (df_funcionarios["nome"].str.strip().str.lower() == nome.strip().lower())
        & (df_funcionarios["matricula"].str.strip() == matricula.strip())
    ]
    return not resultado.empty




def autenticar_sessao(session_id: str, nome: str = None, matricula: str = None) -> tuple[bool, str]:
    """
    Garante que a sessao esta autenticada antes de liberar as ferramentas
    de credito/cobranca. Retorna (autenticado, mensagem).
    """
    if session_id in sessao_funcionario:
        return True, ""

    if nome and matricula:
        if validar_funcionario(nome, matricula):
            sessao_funcionario[session_id] = {"nome": nome, "matricula": matricula}
            return True, ""
        return False, "Nome ou matrícula não conferem com o cadastro. Por favor, confirme os dados."

    return False, (
        "Para responder isso preciso confirmar seu cadastro. "
        "Por favor, informe seu nome completo e matrícula de funcionário."
    )


# ---------------------------------------------------------------------------
# Conteudo institucional (nao exige autenticacao)
# ---------------------------------------------------------------------------
CONTEUDO_INSTITUCIONAL = """\
SOBRE A PETROMAX QUÍMICA
 
Origem:
Em 2011, no coração do polo petroquímico de Camaçari (BA) — um dos \
maiores complexos industriais do Hemisfério Sul —, o engenheiro químico \
Everton Ferreira Guedes identificou uma lacuna que o mercado insistia em \
ignorar: pequenas e médias indústrias da região tinham acesso limitado a \
insumos petroquímicos de qualidade, com prazos de entrega pouco confiáveis \
e suporte técnico quase inexistente. Foi a partir dessa constatação, e não \
de um plano de negócios ambicioso, que nasceu a PetroMax Química: um \
galpão alugado, duas máquinas de mistura adquiridas de segunda mão e uma \
equipe de três pessoas dispostas a provar que rigor técnico e proximidade \
com o cliente não precisavam ser privilégio das grandes corporações.
 
O teste decisivo:
Os primeiros dois anos exigiram mais disciplina do que capital. Sem \
margem para erros, a equipe se dedicou a dominar cada etapa do processo \
produtivo antes de buscar crescimento. Essa base sólida se provou \
essencial em 2013, quando a PetroMax fechou seu primeiro contrato de \
fornecimento contínuo com uma fabricante de tintas industriais de grande \
porte — um cliente que não abria mão de consistência química e \
pontualidade absoluta. A entrega bem-sucedida desse contrato não apenas \
validou o modelo de negócio: tornou-se a referência que impulsionou a \
reputação da empresa em todo o setor.
 
Consolidação e expansão:
Na década seguinte, a PetroMax Química ampliou sua capacidade produtiva, \
diversificou seu portfólio e investiu continuamente em controle de \
qualidade e capacitação técnica de sua equipe. Cresceu sem abrir mão do \
princípio fundador: cada cliente deve sentir que está lidando com uma \
empresa que conhece profundamente sua química — e seu negócio.
 
O presente: tecnologia a serviço da operação:
Hoje, a PetroMax Química une a experiência acumulada de mais de uma \
década de chão de fábrica a uma gestão orientada por dados e tecnologia. \
Este assistente virtual é um exemplo direto dessa filosofia: fruto do \
projeto interno de inovação **One AI Tech Builder**, idealizado para \
aproximar inteligência artificial da rotina operacional, comercial e de \
relacionamento com o cliente — tornando processos mais ágeis sem abrir \
mão da precisão que sempre foi a marca registrada da empresa.
 
Fundador e Diretor Geral: Everton Ferreira Guedes.
 
Portfólio de produtos:
- Resinas e polímeros industriais
- Solventes e diluentes técnicos
- Aditivos para tintas e vernizes
- Insumos petroquímicos sob medida (formulação customizada por cliente)
- Lubrificantes industriais especiais
 
Nossa equipe:
- Corpo fabril: aproximadamente 140 colaboradores, organizados em três \
turnos de produção contínua
- Corpo administrativo e comercial: aproximadamente 35 colaboradores
 
Horário de funcionamento:
- Produção (fábrica): operação contínua em 3 turnos, 24 horas por dia, \
de segunda a sábado
- Administrativo e Comercial: segunda a sexta-feira, das 8h às 18h \
(horário de Brasília)
 
Do galpão alugado em Camaçari à operação de hoje, a PetroMax Química \
segue orientada pelo mesmo compromisso que a fundou: ciência aplicada, \
agilidade e proximidade genuína com quem confia em nossos produtos — \
agora potencializados por inteligência artificial.
"""


@tool
def informacoes_institucionais(pergunta: str) -> str:
    """Responde perguntas sobre a empresa: história, fundador, produtos,
    número de funcionários e horários de funcionamento. Não requer cadastro."""
    return CONTEUDO_INSTITUCIONAL


# ---------------------------------------------------------------------------
# Ferramentas de credito / cobranca (ja existentes)
# ---------------------------------------------------------------------------
@tool
def verificar_credito(cpf: str) -> dict:
    """
    Verifica o limite de crédito, valor utilizado e disponível de um
    cliente pelo CPF.
    """
    return biz.verificar_credito(cpf)


@tool
def identificar_cliente_por_cpf(cpf: str) -> dict:
    """Identifica um cliente da PetroMax Quimica a partir do CPF informado,
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
def gerar_relatorio_inadimplencia_geral(motivo_consulta: str = "geral") -> dict:
    """Gera um relatório gerencial de inadimplência de toda a carteira de
    clientes, com faixas de atraso (aging: 0-30, 31-60, 61-90, 90+ dias).
    O parâmetro motivo_consulta pode ser preenchido com qualquer texto ou
    deixado no padrão."""
    return biz.gerar_relatorio_inadimplencia_geral()


TOOLS_COMERCIAIS = [
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

# Todas as ferramentas do agente: comerciais + institucional
TOOLS = TOOLS_COMERCIAIS + [informacoes_institucionais]

SYSTEM_PROMPT = """\
Você é o Agente PetroMax, assistente virtual institucional e de crédito e \
cobrança da PetroMax Química, uma empresa do setor petroquímico.

Seu papel é:
- Responder perguntas institucionais (história, fundador, produtos, número \
de funcionários, horários de funcionamento) para qualquer pessoa, sem \
exigir cadastro.
- Ajudar colaboradores(as) do time financeiro e de atendimento com \
crédito e cobrança: identificar clientes pelo CPF, consultar crédito, \
boletos, descontos, juros/multa, 2ª via, comprovantes, histórico e score \
de pagamento, restrição SPC/Serasa, bloqueio/liberação de pedidos, \
parcelamento de dívidas, contestações e relatórios de inadimplência.

Regras:
1. Sempre que a pergunta envolver um cliente específico, peça o CPF caso \
não tenha sido informado.
2. Use as ferramentas disponíveis para buscar dados reais — nunca invente \
valores, datas ou status.
3. Responda sempre em português, de forma clara e profissional.
4. Ao apresentar valores monetários, use o formato R$ 0.000,00.
"""


def build_agent() -> AgentExecutor:
    """Constrói e retorna o AgentExecutor pronto para uso."""
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


# ---------------------------------------------------------------------------
# Ponto de entrada para o chat: aplica o gate de autenticacao ANTES de
# chamar o agente, para as perguntas comerciais/credito.
# ---------------------------------------------------------------------------
_agent_executor = None


def responder(pergunta: str, session_id: str, nome: str = None, matricula: str = None) -> str:
    """
    Ponto único de entrada usado pelo chat.
    - Perguntas institucionais: sempre liberadas.
    - Perguntas comerciais/crédito: exigem autenticação de funcionário
      (nome + matrícula) na primeira vez de cada sessão.
    """
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = build_agent()

    # Heurística simples: se a sessão ainda não está autenticada E a
    # pergunta não é claramente institucional, pede o cadastro antes de
    # acionar o agente (evita que ferramentas de crédito sejam chamadas
    # sem autenticação).
    palavras_institucionais = [
        "história", "fundador", "fundação", "quando foi fundad",
        "produtos", "quantos funcionários", "horário de funcionamento",
        "sobre a empresa", "sobre a petromax",
    ]
    e_institucional = any(p in pergunta.lower() for p in palavras_institucionais)

    if not e_institucional:
        autenticado, mensagem = autenticar_sessao(session_id, nome, matricula)
        if not autenticado:
            return mensagem

    resultado = _agent_executor.invoke({"input": pergunta})
    return resultado["output"]