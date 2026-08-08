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
    user_login: Optional[str] = None


class ChatSessionRepositoryPostgres:
    def __init__(self):
        self._logger = get_logger(__name__)
        self._table_created = False
        self._ensure_table()

    def _ensure_table(self) -> None:
        if self._table_created:
            return
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            session_id VARCHAR(255) NOT NULL,
                            user_login VARCHAR(255),
                            title VARCHAR(255) NOT NULL,
                            history JSONB NOT NULL DEFAULT '[]'::jsonb,
                            disease VARCHAR(255),
                            symptom_list JSONB NOT NULL DEFAULT '[]'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                        ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_login VARCHAR(255);
                        CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions (session_id);
                        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_login ON chat_sessions (user_login);
                        CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions (updated_at DESC);
                        """
                    )
            self._table_created = True
        except Exception as exc:
            self._logger.error("Erro ao garantir tabela chat_sessions no PostgreSQL: %s", exc)

    def list_by_user(self, user_login: str) -> List[ChatSession]:
        """Lista todos os chats salvos pertencentes a um usuário (login)."""
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at, user_login
                    FROM chat_sessions
                    WHERE LOWER(user_login) = %s
                    ORDER BY updated_at DESC
                    """,
                    (user_login.strip().lower(),),
                )
                rows = cur.fetchall()
                return [self._row_to_model(r) for r in rows]

    def list_by_session(self, session_id: str) -> List[ChatSession]:
        """Lista todos os chats salvos de uma session_id."""
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at, user_login
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
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at, user_login
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                    LIMIT 200
                    """
                )
                rows = cur.fetchall()
                return [self._row_to_model(r) for r in rows]

    def get_by_id(self, chat_id: str) -> Optional[ChatSession]:
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, session_id, title, history, disease, symptom_list,
                           created_at, updated_at, user_login
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
        user_login: Optional[str] = None,
        chat_id: Optional[str] = None,
    ) -> ChatSession:
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                if chat_id:
                    cur.execute(
                        """
                        UPDATE chat_sessions
                        SET history = %s::jsonb, disease = %s, symptom_list = %s::jsonb, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING id, session_id, title, history, disease, symptom_list,
                                  created_at, updated_at, user_login
                        """,
                        (
                            json.dumps(history),
                            disease,
                            json.dumps(symptom_list or []),
                            chat_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row:
                        self._logger.info(f"Chat atualizado: {chat_id} (session={session_id})")
                        return self._row_to_model(row)

                cur.execute(
                    """
                    INSERT INTO chat_sessions (session_id, title, history, disease, symptom_list, user_login)
                    VALUES (%s, %s, %s::jsonb, %s, %s::jsonb, %s)
                    RETURNING id, session_id, title, history, disease, symptom_list,
                              created_at, updated_at, user_login
                    """,
                    (
                        session_id,
                        title,
                        json.dumps(history),
                        disease,
                        json.dumps(symptom_list or []),
                        user_login.strip().lower() if user_login else None,
                    ),
                )
                row = cur.fetchone()
                self._logger.info(f"Chat salvo: {row[0]} (session={session_id}, user={user_login})")
                return self._row_to_model(row)

    def update_title(self, chat_id: str, title: str) -> Optional[ChatSession]:
        self._ensure_table()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE chat_sessions
                    SET title = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id, session_id, title, history, disease, symptom_list,
                              created_at, updated_at, user_login
                    """,
                    (title.strip(), chat_id),
                )
                row = cur.fetchone()
                if row:
                    self._logger.info(f"Chat renomeado: {chat_id} -> '{title}'")
                    return self._row_to_model(row)
                return None

    def delete(self, chat_id: str) -> bool:
        self._ensure_table()
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

        user_login = row[8] if len(row) > 8 else None

        return ChatSession(
            id=row[0],
            session_id=row[1],
            title=row[2],
            history=history or [],
            disease=row[4],
            symptom_list=symptom_list or [],
            created_at=row[6],
            updated_at=row[7],
            user_login=user_login,
        )
