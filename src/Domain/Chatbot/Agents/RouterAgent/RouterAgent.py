from src.SharedKernel.Logging.Logger import get_logger
from src.Domain.Chatbot.Abstractions.AgentInterface import AgentInterface, AgentType, AgentResponse


class RouterAgent(AgentInterface):
    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)

    async def generate_response(self, message: str) -> AgentResponse:
        try:
            user_message = message or ""
            agent_result = await self.llm.process(user_message)

            predicted_agent = (agent_result.message or "").strip().lower()

            if not predicted_agent or predicted_agent not in ["sintomas", "conversation", "final", "fallback"]:
                predicted_agent = "sintomas"

            return AgentResponse(
                agent_type=AgentType.NEXT,
                next_agent=predicted_agent
            )

        except Exception as e:
            self.logger.error(f"Erro no RouterAgent: {str(e)}")
            return AgentResponse(
                agent_type=AgentType.NEXT,
                next_agent="sintomas"
            )
