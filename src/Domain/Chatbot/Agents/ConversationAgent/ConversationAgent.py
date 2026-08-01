from src.Domain.Chatbot.Abstractions.AgentInterface import (
    AgentInterface,
    AgentResponse,
    AgentType,
)
from src.SharedKernel.Logging.Logger import get_logger


class ConversationAgent(AgentInterface):
    """
    Agente responsável por manter a conversa geral entre médico e paciente.
    Ele usa o histórico fornecido no prompt para responder como paciente,
    garantindo continuidade e naturalidade antes de direcionar para sintomas.
    """

    def __init__(self, llm):
        super().__init__(llm)
        self.logger = get_logger(__name__)
        self.default_next_agent = "conversation"
        self.symptom_request_keywords = [
            "sintoma",
            "dor",
            "dores",
            "sentindo",
            "sente",
            "sente alguma",
            "sentiu",
            "alguma coisa",
            "o que sente",
            "o que está sentindo",
            "há quanto tempo",
            "desde quando",
            "descreva",
            "me fale",
            "me diga",
            "quais são",
            "onde dói",
            "onde sente",
        ]

    async def generate_response(self, message: str) -> AgentResponse:
        """
        Mantém a conversa como paciente e indica qual agente deve responder em seguida.
        """
        try:
            user_message = message or ""
            llm_response = await self.llm.process(user_message)
            reply = (llm_response.message or "").strip()

            if not reply:
                reply = "Doutor, não entendi muito bem. Poderia repetir de outra forma?"

            next_agent = self._decide_next_agent(user_message)

            return AgentResponse(
                agent_type=AgentType.FINAL,
                message=reply,
                next_agent=next_agent,
            )
        except Exception as exc:
            self.logger.error(f"Erro no ConversationAgent: {str(exc)}")
            return AgentResponse(
                agent_type=AgentType.FINAL,
                message="Desculpe doutor, acho que me confundi um pouco agora.",
                next_agent=self.default_next_agent,
            )

    def _decide_next_agent(self, user_message: str) -> str:
        if self._is_symptom_request(user_message):
            return "sintomas"
        return self.default_next_agent

    def _is_symptom_request(self, user_message: str) -> bool:
        if not user_message:
            return False

        normalized = user_message.lower()
        return any(keyword in normalized for keyword in self.symptom_request_keywords)

