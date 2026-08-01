from abc import ABC, abstractmethod

from src.Domain.Interfaces.Llm.LlmInterface import LlmConfig, LlmInterface


class LlmProviderResolver(ABC):

    @abstractmethod
    def resolve(
        self,
        llm_type: str,
        config: LlmConfig,
        system_prompt: str,
    ) -> LlmInterface:

        raise NotImplementedError

