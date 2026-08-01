"""
SintomasAgent — responde perguntas sobre sintomas do paciente.

Usa o LLM configurado em SintomasAgentConfig. O histórico de conversa
é injetado no prompt via ChatCommandHandler antes da chamada ao agente.
"""
from src.Domain.Chatbot.Abstractions.AgentInterface import AgentInterface, AgentType, AgentResponse
from src.SharedKernel.Logging.Logger import get_logger


class SintomasAgent(AgentInterface):
    """
    Handler responsável por processar mensagens relacionadas aos sintomas do paciente
    durante a anamnese. O prompt já contém os sintomas, a doença e o histórico de
    conversa — o agente apenas precisa gerar a resposta do paciente.
    """

    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)

    async def generate_response(self, message: str) -> AgentResponse:
        """
        Processa a mensagem e retorna a resposta do paciente sobre sintomas.
        """
        try:
            agent_response = await self.llm.process(message)
            reply = (agent_response.message or "").strip()

            if not reply:
                reply = "Desculpe doutor, pode repetir?"

            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=reply,
                next_agent="sintomas",
            )

        except Exception as e:
            self.logger.error(f"Erro no SintomasAgent: {str(e)}")
            return AgentResponse(
                agent_type=AgentType.FINAL,
                message="Desculpe doutor, estou com dificuldade para explicar melhor agora.",
                next_agent=None,
            )