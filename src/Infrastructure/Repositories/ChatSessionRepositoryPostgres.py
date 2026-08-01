"""
Repositório de sessões de chat persistidas no PostgreSQL.
Permite salvar, listar, recuperar e deletar históricos de consulta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.Infrastructure.Database.Connection import get_connection
from src.SharedKernel.Logging.Logger import get_logger

import json


@dataclass
class ChatSession:
    id: UUID
    session_id: str
    title: str
    history: List[Dict[str, Any]]
    disease: Optional[str]
    symptom_list: List[str]
    created_at: datetime
    updated_at: datetime


class ChatSessionRepositoryPostgres:
    def __init__(self):
        self._logger = get_logger(__name__)

    def list_by_session(self, session_id: str) -> List[ChatSession]:
        """Lista todos os chats salvos de uma session_id."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at
                    FROM chat_sessions
                    WHERE session_id = %s
                    ORDER BY updated_at DESC
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()
                return [self._row_to_model(r) for r in rows]

    def list_all(self) -> List[ChatSession]:
        """Lista todos os chats (para uso admin)."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
                return [self._row_to_model(r) for r in rows]

    def get_by_id(self, chat_id: str) -> Optional[ChatSession]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at
                    FROM chat_sessions WHERE id = %s
                    """,
                    (chat_id,),
                )
                row = cur.fetchone()
                return self._row_to_model(row) if row else None

    def save(
        self,
        session_id: str,
        title: str,
        history: List[Dict[str, Any]],
        disease: Optional[str] = None,
        symptom_list: Optional[List[str]] = None,
    ) -> ChatSession:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, title, history, disease, symptom_list)
                    VALUES (%s, %s, %s::jsonb, %s, %s::jsonb)
                    RETURNING id, session_id, title, history, disease, symptom_list,
                              created_at, updated_at
                    """,
                    (
                        session_id,
                        title,
                        json.dumps(history),
                        disease,
                        json.dumps(symptom_list or []),
                    ),
                )
                row = cur.fetchone()
                self._logger.info(f"Chat salvo: {row[0]} (session={session_id})")
                return self._row_to_model(row)

    def delete(self, chat_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM chat_sessions WHERE id = %s RETURNING id",
                    (chat_id,),
                )
                deleted = cur.fetchone()
                if deleted:
                    self._logger.info(f"Chat deletado: {chat_id}")
                return deleted is not None

    def _row_to_model(self, row) -> ChatSession:
        history = row[3]
        if isinstance(history, str):
            history = json.loads(history)

        symptom_list = row[5]
        if isinstance(symptom_list, str):
            symptom_list = json.loads(symptom_list)

        return ChatSession(
            id=row[0],
            session_id=row[1],
            title=row[2],
            history=history or [],
            disease=row[4],
            symptom_list=symptom_list or [],
            created_at=row[6],
            updated_at=row[7],
        )
