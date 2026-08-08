from src.Domain.Chatbot.Abstractions.AgentInterface import (
    AgentInterface,
    AgentResponse,
    AgentType,
)
from src.SharedKernel.Logging.Logger import get_logger


class ConversationAgent(AgentInterface):
    """
    Agente responsável por manter a conversa geral entre médico e paciente.
    Responde como paciente e para a execução do loop — o roteamento da próxima
    mensagem é sempre responsabilidade do RouterAgent.
    """

    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)

    async def generate_response(self, message: str) -> AgentResponse:
        """
        Responde como paciente e sempre encerra o loop com AgentType.FINAL.
        O RouterAgent decidirá o próximo agente na próxima mensagem do médico.
        """
        try:
            user_message = message or ""
            llm_response = await self.llm.process(user_message)
            reply = (llm_response.message or "").strip()

            if not reply:
                reply = "Doutor, não entendi muito bem. Poderia repetir de outra forma?"

            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=reply,
                next_agent=None,
            )
        except Exception as exc:
            self.logger.error(f"Erro no ConversationAgent: {str(exc)}")
            return AgentResponse(
                agent_type=AgentType.FINAL,
                message="Desculpe doutor, acho que me confundi um pouco agora.",
                next_agent=None,
            )
