from typing import Dict, Optional, Type

from src.Domain.Interfaces.Llm.LlmInterface import LlmInterface, LlmConfig
from src.Domain.Interfaces.Llm.LlmProviderResolver import LlmProviderResolver
from src.SharedKernel.Messages.Exceptions import AgentTypeNotFoundError
from src.Infrastructure.Llm.GemniLlm import GeminiLlm
from src.Infrastructure.Llm.LangChainOpenAILlm import LangChainOpenAILlm


class DefaultLlmProviderResolver(LlmProviderResolver):


    def __init__(
        self,
        providers: Optional[Dict[str, Type[LlmInterface]]] = None,
    ) -> None:
        self._providers: Dict[str, Type[LlmInterface]] = {}
        self._register_default_providers()

        if providers:
            for name, provider in providers.items():
                self.register(name, provider)

    def register(self, name: str, provider: Type[LlmInterface]) -> None:
        if not name:
            raise ValueError("Nome do provedor não pode ser vazio")

        normalized = name.lower().strip()
        if not normalized:
            raise ValueError("Nome do provedor não pode conter apenas espaços")

        self._providers[normalized] = provider

    def resolve(
        self,
        llm_type: str,
        config: LlmConfig,
        system_prompt: str,
    ) -> LlmInterface:
        if not llm_type:
            raise AgentTypeNotFoundError("Tipo de LLM não informado")

        provider_cls = self._providers.get(llm_type.lower())
        if not provider_cls:
            raise AgentTypeNotFoundError(f"Tipo de LLM não registrado: {llm_type}")

        return provider_cls(config=config, system_prompt=system_prompt)

    def available_types(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def _register_default_providers(self) -> None:
        self.register("gemini", GeminiLlm)
        # Usa LangChainOpenAILlm como provider padrão: async nativo, sem asyncio.to_thread
        self.register("gpt", LangChainOpenAILlm)

