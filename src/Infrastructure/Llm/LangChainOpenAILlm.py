"""
LangChain LLM wrapper that implements LlmInterface.

Usa ChatOpenAI do LangChain com ChatPromptTemplate para injeção do system prompt,
mantendo compatibilidade com a interface de agentes existente.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.Domain.Interfaces.Llm.LlmInterface import LlmInterface, LlmResponse, LlmConfig
from src.SharedKernel.Logging.Logger import get_logger


def _get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        src_dir = Path(__file__).resolve().parents[2]
        env_path = src_dir.parent / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente!")
    return api_key


class LangChainOpenAILlm(LlmInterface):
    """
    Implementação de LlmInterface usando LangChain ChatOpenAI.

    Mantém a mesma interface pública (process(message) → LlmResponse),
    mas usa o pipeline LangChain internamente, facilitando futuras extensões
    (streaming, ferramentas, memória estruturada, etc.).
    """

    def __init__(self, config: LlmConfig, system_prompt: str):
        super().__init__(config, system_prompt)
        self._logger = get_logger(__name__)

        self._llm = ChatOpenAI(
            model=config.model,
            max_tokens=config.max_completion_tokens,
            api_key=_get_openai_api_key(),
            temperature=0.7,
        )

        self._prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("human", "{user_message}"),
            ]
        )

        self._chain = self._prompt | self._llm | StrOutputParser()

    async def process(self, message: str) -> LlmResponse:
        if not message:
            raise ValueError("Mensagem vazia não é permitida")

        try:
            content = await self._chain.ainvoke(
                {
                    "system_prompt": self.system_prompt,
                    "user_message": message,
                }
            )
            return LlmResponse(message=content.strip())

        except Exception as exc:
            self._logger.error(f"Erro no LangChainOpenAILlm: {exc}", exc_info=True)
            raise
