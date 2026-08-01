from src.Domain.Chatbot.Abstractions.AgentInterface import (
    AgentInterface,
    AgentResponse,
    AgentType,
)
from src.SharedKernel.Logging.Logger import get_logger


class FallbackAgent(AgentInterface):

    def __init__(self, llm=None):
        super().__init__(llm)
        self.logger = get_logger(__name__)

    async def generate_response(self, message: str) -> AgentResponse:
        try:
            last_message = message or ""

            agent_response = await self.llm.process(message)
            response_text = (agent_response.message or "").strip()

            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=response_text,
                next_agent=None
            )

        except Exception as e:
            self.logger.error(f"Erro no FallbackAgent: {str(e)}")
            return AgentResponse(
                agent_type=AgentType.FINAL,
                message="Ocorreu um erro inesperado ao processar sua mensagem.",
                next_agent=None
            )
