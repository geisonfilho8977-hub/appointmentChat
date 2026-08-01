from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, Field

from src.Domain.Interfaces.Llm.LlmInterface import LlmInterface


class AgentType(Enum):
    NEXT = "next"
    FINAL = "final"


class AgentResponse(BaseModel):
    agent_type: AgentType
    next_agent: str | None = None
    message: str | None = None
    payload: dict = Field(default_factory=dict)


class AgentInterface(ABC):
    def __init__(self, llm: LlmInterface):
        self.llm = llm

    @abstractmethod
    async def generate_response(self, message: str) -> AgentResponse:
        """
        Gera uma resposta do agente com base na mensagem do usuário.
        """
        raise NotImplementedError
