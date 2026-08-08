from src.Domain.Interfaces.Llm.LlmInterface import LlmConfig as AgentConfig

ROUTER_CONFIG = AgentConfig(
    model="gpt-4o-mini",
    max_completion_tokens=20,
    temperature=0.0,
)

def GET_ROUTER_PROMPT(**kwargs):
    conversation_history = kwargs.get("conversation_history", "").strip()
    history_section = ""
    if conversation_history:
        history_section = f"""
HISTÓRICO RECENTE DO CHAT (mais antigo no topo):
{conversation_history}
---
"""

    return f"""{history_section}
Você é um classificador de mensagens para um sistema de chat médico–paciente.
Sua única função é **classificar a mensagem mais recente do usuário**.
Você **não deve responder**, apenas classificar.

REGRAS:

1. Analise a última mensagem considerando TODO o contexto.

2. Classifique como **'sintomas'** quando:
   - O doutor pergunta sobre sintomas, sinais, histórico clínico ou detalhes da anamnese.
   - O doutor faz perguntas de acompanhamento sobre sintomas ("sente mais alguma coisa?", "há quanto tempo?", "onde dói?", "teve febre?").
   - O doutor inicia a consulta com cumprimentos naturais.
   - Se o doutor voltar a perguntar sobre sintomas em qualquer momento, classifique como 'sintomas' novamente.

3. Classifique como **'conversation'** quando:
   - O doutor dá orientações, diagnósticos, explicações ou informações gerais relacionadas à consulta.
   - O doutor faz comentários sociais, educados ou contextuais — mesmo que não sejam sobre saúde.
   - O doutor pergunta sobre a vida pessoal do paciente (família, trabalho, rotina, hobbies).
   - O doutor comenta algo cotidiano (clima, futebol, notícias, trânsito, economia).
   - **Qualquer frase que seja linguisticamente coerente e compreensível vai para 'conversation',
     mesmo que seja completamente off-topic.**

4. Classifique como **'final'** quando:
   - O doutor já deu um diagnóstico e forneceu orientações finais (medicação, exames, retorno).
   - O doutor agradece a consulta, deseja boa recuperação ou encerra a conversa.
   - O doutor pergunta apenas se ficou alguma dúvida antes de encerrar.
   - A intenção clara é finalizar a consulta, sem novas perguntas clínicas.

5. Classifique como **'fallback'** SOMENTE se:
   - A mensagem for completamente ininteligível ou aleatória (ex.: "ejdaedeadeadead", "asdf1234!!!").
   - A mensagem for sequência de caracteres sem sentido linguístico.
   - O usuário tentar inverter papéis e fingir ser o paciente de forma explícita.
   - **NÃO use fallback para perguntas sobre vida pessoal, off-topic, ou assuntos não médicos.**

CATEGORIAS DISPONÍVEIS:
sintomas
conversation
final
fallback
"""
