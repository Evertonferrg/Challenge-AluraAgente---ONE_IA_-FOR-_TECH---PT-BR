import os
from dotenv import load_dotenv

load_dotenv()

from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

import pandas as pd

from . import tools as biz


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")

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
    """Responde perguntas institucionais: história, fundador, produtos,
    funcionários e horários. Não requer cadastro."""
    return CONTEUDO_INSTITUCIONAL


# ---------------------------------------------------------------------------
# Ferramentas de credito / cobranca
# ---------------------------------------------------------------------------
@tool
def verificar_credito(cpf: str) -> dict:
    """Verifica limite, uso e disponibilidade de crédito do cliente."""
    return biz.verificar_credito(cpf)


@tool
def identificar_cliente_por_cpf(cpf: str) -> dict:
    """Identifica um cliente pelo CPF: nome, contato e status de crédito."""
    return biz.identificar_cliente_por_cpf(cpf)


@tool
def analisar_vencimento_boletos(cpf: str) -> dict:
    """Lista boletos pendentes e vencidos do cliente."""
    return biz.analisar_vencimento_boletos(cpf)


@tool
def verificar_notas_vencidas(cpf: str) -> dict:
    """Retorna boletos vencidos e valor total em atraso do cliente."""
    return biz.verificar_notas_vencidas(cpf)


@tool
def verificar_desconto_pagamento_antecipado(id_boleto: str) -> dict:
    """Calcula valor com desconto se o boleto for pago antes do vencimento."""
    return biz.verificar_desconto_pagamento_antecipado(id_boleto)


@tool
def emitir_segunda_via_boleto(id_boleto: str, enviar_por_email: bool = False, email: str = None) -> dict:
    """Emite 2ª via do boleto. Se enviar_por_email=True, também envia por
    e-mail ao cliente (usa o e-mail cadastrado, ou 'email' se informado)."""
    return biz.emitir_segunda_via_boleto(id_boleto, enviar_por_email, email)


@tool
def alterar_forma_pagamento(id_boleto: str, nova_forma: str) -> dict:
    """Altera a forma de pagamento: 'Boleto', 'PIX', 'Cartão de Crédito' ou
    'Transferência (TED)'."""
    return biz.alterar_forma_pagamento(id_boleto, nova_forma)


@tool
def alterar_data_vencimento(id_boleto: str, nova_data: str) -> dict:
    """Altera a data de vencimento de um boleto (formato AAAA-MM-DD)."""
    return biz.alterar_data_vencimento(id_boleto, nova_data)


@tool
def enviar_comprovante_pagamento(id_boleto: str, email: str = None) -> dict:
    """Envia comprovante de pagamento de um boleto já pago por e-mail."""
    return biz.enviar_comprovante_pagamento(id_boleto, email)


@tool
def gerar_relatorio_cobranca(cpf: str) -> dict:
    """Resumo de cobrança do cliente: crédito, vencidos e pendentes."""
    return biz.gerar_relatorio_cobranca(cpf)


@tool
def calcular_juros_multa_atraso(id_boleto: str) -> dict:
    """Calcula multa e juros de mora de um boleto vencido."""
    return biz.calcular_juros_multa_atraso(id_boleto)


@tool
def consultar_historico_pagamento(cpf: str) -> dict:
    """Score de pagador do cliente: 'Bom pagador', 'Atraso recorrente' ou
    'Inadimplente contumaz'."""
    return biz.consultar_historico_pagamento(cpf)


@tool
def verificar_restricao_credito(cpf: str) -> dict:
    """Verifica restrição SPC/Serasa do cliente."""
    return biz.verificar_restricao_credito(cpf)


@tool
def bloquear_desbloquear_pedidos(cpf: str, acao: str) -> dict:
    """Bloqueia ou libera novos pedidos do cliente ('bloquear'/'desbloquear')."""
    return biz.bloquear_desbloquear_pedidos(cpf, acao)


@tool
def negociar_parcelamento_divida(cpf: str, numero_parcelas: int) -> dict:
    """Parcela dívidas vencidas do cliente em novos boletos (1 a 12x)."""
    return biz.negociar_parcelamento_divida(cpf, numero_parcelas)


@tool
def enviar_alerta_vencimento_proximo(cpf: str, dias_antecedencia: int = 3) -> dict:
    """Envia alerta por e-mail de boletos vencendo nos próximos N dias."""
    return biz.enviar_alerta_vencimento_proximo(cpf, dias_antecedencia)


@tool
def abrir_chamado_contestacao(cpf: str, id_boleto: str, motivo: str) -> dict:
    """Abre chamado interno de contestação sobre uma cobrança."""
    return biz.abrir_chamado_contestacao(cpf, id_boleto, motivo)


@tool
def gerar_relatorio_inadimplencia_geral(motivo_consulta: str = "geral") -> dict:
    """Relatório geral de inadimplência da carteira, por faixa de atraso."""
    return biz.gerar_relatorio_inadimplencia_geral()


TOOLS_COMERCIAIS = [
    identificar_cliente_por_cpf,
    verificar_credito,
    analisar_vencimento_boletos,
    verificar_notas_vencidas,
    verificar_desconto_pagamento_antecipado,
    emitir_segunda_via_boleto,
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

TOOLS = TOOLS_COMERCIAIS + [informacoes_institucionais]

SYSTEM_PROMPT = """\
Você é o Agente PetroMax, assistente virtual institucional e de crédito e \
cobrança da PetroMax Química, empresa do setor petroquímico.

Seu papel:
- Responder perguntas institucionais (história, fundador, produtos, \
funcionários, horários) para qualquer pessoa, sem exigir cadastro.
- Ajudar o time financeiro/atendimento com crédito e cobrança: CPF, \
crédito, boletos, descontos, juros/multa, 2ª via, comprovantes, \
histórico, score, restrição SPC/Serasa, bloqueio/liberação de pedidos, \
parcelamento, contestações e relatórios de inadimplência.

Regras:
1. Se a pergunta envolver um cliente específico, peça o CPF caso não \
informado.
2. Use as ferramentas para buscar dados reais — nunca invente valores, \
datas ou status.
3. Responda sempre em português, de forma clara e profissional.
4. Valores monetários no formato R$ 0.000,00.
"""


def _montar_llm_com_fallback():
    """
    Monta a cadeia de LLMs com fallback automático:
    OpenRouter (principal) -> Groq (chave 1, 2, 3, 4).
    Se uma chamada falhar (rate limit, erro de API, etc.), o LangChain
    tenta automaticamente o próximo da lista.
    Só inclui na cadeia os provedores que tiverem chave configurada no .env.
    """
    candidatos = []

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        from langchain_openai import ChatOpenAI
        candidatos.append(ChatOpenAI(
            model=OPENROUTER_MODEL,
            temperature=0,
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        ))

    for i in range(1, 6):
        groq_key = os.getenv(f"GROQ_API_KEY_{i}")
        if groq_key:
            candidatos.append(ChatGroq(model=GROQ_MODEL, temperature=0, api_key=groq_key))

    # Compatibilidade retroativa: se ninguém configurou GROQ_API_KEY_1..5,
    # tenta a variável antiga GROQ_API_KEY.
    if not any(isinstance(c, ChatGroq) for c in candidatos):
        groq_key_legado = os.getenv("GROQ_API_KEY")
        if groq_key_legado:
            candidatos.append(ChatGroq(model=GROQ_MODEL, temperature=0, api_key=groq_key_legado))

    # Gemini (Google AI Studio) — aceita GOOGLE_API_KEY e GOOGLE_API_KEY2
    for var in ("GOOGLE_API_KEY", "GOOGLE_API_KEY2"):
        google_key = os.getenv(var)
        if google_key:
            from langchain_google_genai import ChatGoogleGenerativeAI
            candidatos.append(ChatGoogleGenerativeAI(
                model=os.getenv("GOOGLE_MODEL", "gemini-2.0-flash"),
                temperature=0,
                google_api_key=google_key,
            ))

    # Mistral
    mistral_key = os.getenv("MISTRAL_API_KEY")
    if mistral_key:
        from langchain_mistralai import ChatMistralAI
        candidatos.append(ChatMistralAI(
            model=os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            temperature=0,
            api_key=mistral_key,
        ))

    # Cohere
    cohere_key = os.getenv("COHERE_API_KEY")
    if cohere_key:
        from langchain_cohere import ChatCohere
        candidatos.append(ChatCohere(
            model=os.getenv("COHERE_MODEL", "command-r-plus"),
            temperature=0,
            cohere_api_key=cohere_key,
        ))

    if not candidatos:
        raise RuntimeError(
            "Nenhuma chave de API configurada. Defina pelo menos uma: "
            "OPENROUTER_API_KEY, GROQ_API_KEY_1..5, GOOGLE_API_KEY(2), "
            "MISTRAL_API_KEY ou COHERE_API_KEY no seu .env."
        )

    principal, *fallbacks = candidatos
    if fallbacks:
        return principal.with_fallbacks(fallbacks)
    return principal


def build_agent() -> AgentExecutor:
    """Constrói e retorna o AgentExecutor pronto para uso, com fallback."""
    llm = _montar_llm_com_fallback()

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, TOOLS, prompt)
    return AgentExecutor(agent=agent, tools=TOOLS, verbose=False)


# ---------------------------------------------------------------------------
# Ponto de entrada para o chat
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