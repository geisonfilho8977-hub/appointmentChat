from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel, Field

from src.SharedKernel.Logging.Logger import get_logger


class LlmResponse(BaseModel):
    message: Optional[str] = None
    payload: dict = Field(default_factory=dict)


class LlmConfig(BaseModel):
    model: str
    max_completion_tokens: int


class LlmInterface(ABC):
    def __init__(self, config: LlmConfig, system_prompt: str):
        self.config = config
        self.system_prompt = system_prompt
        self.logger = get_logger(__name__)

    @abstractmethod
    async def process(self, message: str) -> LlmResponse:
        """
        Processa a mensagem usando o LLM e retorna uma resposta.
        """
        raise NotImplementedError