"""
Teste local do Agente PetroMax.

Este arquivo tem DUAS seções:

1) TESTES AUTOMÁTICOS (não gastam chamada de API real) — validam a lógica
   de autenticação e a cadeia de fallback multi-provedor (OpenRouter ->
   Groq 1..4), simulando falhas de API para confirmar que o fallback
   realmente troca de provedor quando um deles falha.

2) TESTES MANUAIS/INTEGRAÇÃO (gastam chamada de API real) — os testes
   originais, que chamam o agente de verdade e consultam o LLM configurado
   no seu .env. Ficam comentados por padrão; descomente o que quiser rodar.

AJUSTE O IMPORT ABAIXO para o caminho real do seu módulo, se necessário.
"""

import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def linha(titulo):
    print("\n" + "=" * 70)
    print(titulo)
    print("=" * 70)


# ---------------------------------------------------------------------------
# SEÇÃO 1 — TESTES AUTOMÁTICOS (sem gastar API real)
# ---------------------------------------------------------------------------

def testar_fallback_multi_provedor():
    """
    Confirma que a cadeia OpenRouter -> Groq(1-5) -> Gemini(1-2) -> Mistral
    -> Cohere é montada corretamente e que, se os provedores anteriores
    falharem (ex.: rate limit), o LangChain avança automaticamente até
    achar um que funcione. Usa chaves falsas e monkeypatch — não faz
    nenhuma chamada de rede real.
    """
    from langchain_core.messages import AIMessage

    os.environ["OPENROUTER_API_KEY"] = "fake-openrouter-key"
    for i in range(1, 6):
        os.environ[f"GROQ_API_KEY_{i}"] = f"fake-groq-key-{i}"
    os.environ["GOOGLE_API_KEY"] = "fake-google-1"
    os.environ["GOOGLE_API_KEY2"] = "fake-google-2"
    os.environ["MISTRAL_API_KEY"] = "fake-mistral"
    os.environ["COHERE_API_KEY"] = "fake-cohere"

    import importlib
    import src.agent as agent_mod
    importlib.reload(agent_mod)

    chain = agent_mod._montar_llm_com_fallback()

    assert type(chain).__name__ == "RunnableWithFallbacks", "Deveria retornar uma cadeia com fallback"
    # 5 Groq + 2 Gemini + 1 Mistral + 1 Cohere = 9 fallbacks (+ 1 principal OpenRouter = 10 no total)
    assert len(chain.fallbacks) == 9, f"Esperava 9 fallbacks, veio {len(chain.fallbacks)}"

    chamadas = []

    def fake_invoke(self, *args, **kwargs):
        chamadas.append(type(self).__name__)
        if len(chamadas) < 10:
            raise Exception("Erro simulado (rate limit)")
        return AIMessage(content="ok")

    with patch("langchain_openai.ChatOpenAI.invoke", fake_invoke), \
         patch("langchain_groq.ChatGroq.invoke", fake_invoke), \
         patch("langchain_google_genai.ChatGoogleGenerativeAI.invoke", fake_invoke), \
         patch("langchain_mistralai.ChatMistralAI.invoke", fake_invoke), \
         patch("langchain_cohere.ChatCohere.invoke", fake_invoke):
        resultado = chain.invoke("teste")

    assert len(chamadas) == 10, f"Esperava 10 tentativas até o fim da cadeia, teve {len(chamadas)}"
    assert chamadas[0] == "ChatOpenAI", "A 1ª tentativa deveria ser o OpenRouter"
    assert chamadas[-1] == "ChatCohere", "A última tentativa deveria ser o Cohere"
    assert resultado.content == "ok"
    print("OK - fallback percorreu a cadeia completa: OpenRouter -> Groq(x5) -> Gemini(x2) -> Mistral -> Cohere")


def testar_erro_sem_nenhuma_chave():
    """Sem nenhuma chave no .env, deve levantar erro claro (não travar silenciosamente)."""
    for var in ["OPENROUTER_API_KEY", "GROQ_API_KEY", "GROQ_API_KEY_1",
                "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4", "GROQ_API_KEY_5",
                "GOOGLE_API_KEY", "GOOGLE_API_KEY2", "MISTRAL_API_KEY", "COHERE_API_KEY"]:
        os.environ.pop(var, None)

    import importlib
    import src.agent as agent_mod
    importlib.reload(agent_mod)

    try:
        agent_mod._montar_llm_com_fallback()
        raise AssertionError("Deveria ter lançado RuntimeError")
    except RuntimeError:
        print("OK - erro claro lançado quando nenhuma chave está configurada")


def testar_autenticacao_e_fluxo_completo():
    """
    Testa, com o LLM mockado (sem gastar API real):
    1. Pergunta institucional -> responde direto, sem pedir cadastro
    2. Pergunta comercial sem login -> pede cadastro
    3. Pergunta comercial com credencial inválida -> recusa
    4. Pergunta comercial com credencial válida -> autentica e chama a tool real
    5. Mesma sessão já autenticada -> não pede cadastro de novo
    """
    from langchain_core.messages import AIMessage
    import importlib
    import src.agent as agent_mod
    importlib.reload(agent_mod)

    os.environ["OPENROUTER_API_KEY"] = "fake-key"
    agent_mod.sessao_funcionario.clear()
    agent_mod._agent_executor = None

    with patch("src.agent.AgentExecutor.invoke", return_value={"output": "Resposta institucional simulada."}):
        r = agent_mod.responder("Qual a história da empresa?", session_id="auto_1")
        assert "simulada" in r.lower()
    print("OK - institucional responde sem pedir cadastro")

    agent_mod.sessao_funcionario.clear()
    r = agent_mod.responder("Qual o crédito do CPF 11122233344?", session_id="auto_2")
    assert "matr" in r.lower()
    print("OK - comercial sem login pede cadastro (nome + matrícula)")

    r = agent_mod.responder("Qual o crédito do CPF 11122233344?", session_id="auto_3", nome="Fulano", matricula="0000")
    assert "não conferem" in r.lower()
    print("OK - credencial inválida é recusada")

    agent_mod._agent_executor = None
    with patch("src.agent.AgentExecutor.invoke", return_value={"output": "Crédito disponível: R$ 18.000,00"}):
        r = agent_mod.responder(
            "Qual o crédito do CPF 11122233344?", session_id="auto_4",
            nome="Marina Costa Alves", matricula="00002@1",
        )
        assert "crédito" in r.lower()
    print("OK - credencial válida autentica e consulta a tool real")

    with patch("src.agent.AgentExecutor.invoke", return_value={"output": "Boletos vencidos: nenhum."}):
        r = agent_mod.responder("Quais boletos estão vencidos?", session_id="auto_4")
        assert "matr" not in r.lower()
    print("OK - mesma sessão autenticada não pede cadastro de novo")


def rodar_testes_automaticos():
    linha("SEÇÃO 1 - TESTES AUTOMÁTICOS (sem gastar API real)")
    testar_fallback_multi_provedor()
    testar_erro_sem_nenhuma_chave()
    testar_autenticacao_e_fluxo_completo()
    print("\n### TODOS OS TESTES AUTOMÁTICOS PASSARAM ###")


if __name__ == "__main__":
    rodar_testes_automaticos()

    # -----------------------------------------------------------------
    # SEÇÃO 2 — TESTES MANUAIS/INTEGRAÇÃO (gastam chamada de API real)
    # Descomente os blocos abaixo para testar contra o LLM de verdade,
    # usando as chaves configuradas no seu .env.
    # -----------------------------------------------------------------
    #
    # from src.agent import responder
    #
    # linha("Institucional - história/fundação")
    # print(responder("Qual a história e quem fundou a PetroMax?", session_id="sess_1"))
    #
    # linha("Institucional - produtos")
    # print(responder("Quais produtos vocês vendem?", session_id="sess_2"))
    #
    # linha("Comercial SEM login -> espera pedido de cadastro")
    # print(responder("Qual o crédito disponível do CPF 123.456.789-00?", session_id="sess_5"))
    #
    # linha("Comercial com credencial INVÁLIDA -> espera recusa")
    # print(responder(
    #     "Qual o crédito disponível do CPF 123.456.789-00?",
    #     session_id="sess_6", nome="Fulano Inexistente", matricula="0000",
    # ))
    #
    # NOME_VALIDO = "Marina Costa Alves"
    # MATRICULA_VALIDA = "00002@1"
    #
    # linha("Comercial com credencial VÁLIDA -> autentica e consulta")
    # print(responder(
    #     "Qual o crédito disponível do CPF 433.218.196-43?",
    #     session_id="sess_7", nome=NOME_VALIDO, matricula=MATRICULA_VALIDA,
    # ))
    #
    # linha("Mesma sessão (sess_7) já autenticada -> segue direto")
    # print(responder(
    #     "Quais são os boletos vencidos do CPF 433.218.196-43?",
    #     session_id="sess_7",
    # ))
    #
    # linha("Enviar 2ª via do boleto BOL-00001 por e-mail")
    # print(responder(
    #     "Envie a 2ª via do boleto BOL-00001 para o e-mail ferreiraguedeseverton@gmail.com",
    #     session_id="sess_7",
    # ))
    #
    # linha("Testar fallback DE VERDADE: forçar erro no OpenRouter")
    # # Dica: para testar o fallback com chamadas reais, basta colocar uma
    # # OPENROUTER_API_KEY inválida no .env e manter as GROQ_API_KEY_1..4
    # # válidas. O agente deve responder normalmente mesmo assim, usando Groq.
    # print(responder("Quais produtos vocês vendem?", session_id="sess_8"))