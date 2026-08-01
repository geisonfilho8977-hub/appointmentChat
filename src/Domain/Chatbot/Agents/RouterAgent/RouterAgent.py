from src.SharedKernel.Logging.Logger import get_logger
from src.Domain.Chatbot.Abstractions.AgentInterface import AgentInterface, AgentType, AgentResponse


class RouterAgent(AgentInterface):
    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)
        self.current_agent = None

    async def generate_response(self, message: str) -> AgentResponse:
        try:
            user_message = message

            if self.current_agent and self._is_follow_up_question(user_message):
                return AgentResponse(
                    agent_type=AgentType.NEXT,
                    next_agent=self.current_agent
                )

            agent_result = await self.llm.process(user_message)

            predicted_agent = (agent_result.message or "").strip().lower()

            if not predicted_agent:
                predicted_agent = "sintomas"

            self.current_agent = predicted_agent

            return AgentResponse(
                agent_type=AgentType.NEXT,
                next_agent=self.current_agent
            )

        except Exception as e:
            self.logger.error(f"Erro no RouterAgent: {str(e)}")
            self.current_agent = "sintomas"
            return AgentResponse(
                agent_type=AgentType.NEXT,
                next_agent="sintomas"
            )

    def _is_follow_up_question(self, message: str) -> bool:
        follow_up_indicators = [
            "como", "pode", "exemplo", "explique",
            "mostre", "e se", "então", "mas", "e",
            "também", "mais detalhes", "melhor",
            "por que", "?", "..."
        ]

        message = message.lower().strip()
        return any(ind in message for ind in follow_up_indicators)
