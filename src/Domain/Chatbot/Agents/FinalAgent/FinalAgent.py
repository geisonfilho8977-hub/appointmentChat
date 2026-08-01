from src.Domain.Chatbot.Abstractions.AgentInterface import (
    AgentInterface,
    AgentResponse,
    AgentType,
)
from src.SharedKernel.Logging.Logger import get_logger


class FinalAgent(AgentInterface):
    """
    Agente responsável por encerrar a consulta quando o médico já forneceu
    diagnóstico e orientações suficientes. Ele agradece, confirma entendimento
    e encerra a conversa mantendo o papel do paciente.
    """

    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)
        self.default_message = (
            "Muito obrigado, doutor. Vou seguir direitinho as suas orientações."
        )

    async def generate_response(self, message: str) -> AgentResponse:
        try:
            user_message = message or ""
            llm_response = await self.llm.process(user_message)
            reply = (llm_response.message or "").strip() or self.default_message

            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=reply,
                next_agent=AgentType.FINAL,
            )
        except Exception as exc:
            self.logger.error(f"Erro no FinalAgent: {str(exc)}")
            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=self.default_message,
                next_agent=AgentType.FINAL,
            )

