"""
Adaptador que conecta o ChatMemoryStore (PostgreSQL) ao BaseChatMessageHistory do LangChain.

Permite que os agentes LangChain usem automaticamente o histórico de mensagens
via RunnableWithMessageHistory e abstrações padrão do LangChain, sem depender do Redis.
"""
from __future__ import annotations

from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from src.Infrastructure.Cache.ChatMemoryStore import ChatMemoryStore
from src.SharedKernel.Logging.Logger import get_logger


class PostgresChatMessageHistory(BaseChatMessageHistory):
    """
    Implementação nativa do BaseChatMessageHistory do LangChain que persiste
    o histórico de conversas diretamente no PostgreSQL.
    """

    def __init__(self, session_id: str, store: ChatMemoryStore):
        self._session_id = session_id
        self._store = store
        self._logger = get_logger(__name__)
        self._messages: List[BaseMessage] = []

    @classmethod
    async def create(cls, session_id: str, store: ChatMemoryStore) -> "PostgresChatMessageHistory":
        """Factory assíncrona: cria e carrega o histórico de mensagens do PostgreSQL."""
        instance = cls(session_id, store)
        await instance._load()
        return instance

    async def _load(self) -> None:
        """Carrega o histórico do PostgreSQL e converte em objetos BaseMessage do LangChain."""
        try:
            memory = await self._store.get_memory(self._session_id)
            if not memory:
                self._messages = []
                return

            raw_history = memory.get("history") or []
            messages: List[BaseMessage] = []
            for entry in raw_history:
                role = entry.get("role", "user")
                content = entry.get("message", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
            self._messages = messages
        except Exception as exc:
            self._logger.error(f"Erro ao carregar histórico do PostgreSQL: {exc}")
            self._messages = []

    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """Adiciona mensagem na coleção de mensagens do LangChain."""
        self._messages.append(message)

    def clear(self) -> None:
        self._messages = []
