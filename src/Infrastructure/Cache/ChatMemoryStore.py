from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from src.Infrastructure.Database.Connection import get_connection
from src.SharedKernel.Logging.Logger import get_logger


class ChatMemoryStore:
    """
    Camada de persistência de memória de chat ativa em PostgreSQL.
    Substituiu o Redis, garantindo que todo o gerenciamento de estado e memória
    do sistema seja feito via LangChain e PostgreSQL sem dependências externas adicionais.
    """

    def __init__(
        self,
        *,
        max_history_entries: int = 500,
    ):
        self._logger = get_logger(__name__)
        self._max_history_entries = max_history_entries
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
                        CREATE TABLE IF NOT EXISTS chat_memories (
                            session_id VARCHAR(255) PRIMARY KEY,
                            disease VARCHAR(255),
                            symptom_list JSONB NOT NULL DEFAULT '[]'::jsonb,
                            history JSONB NOT NULL DEFAULT '[]'::jsonb,
                            patient_profile JSONB,
                            user_login VARCHAR(255),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                        ALTER TABLE chat_memories ADD COLUMN IF NOT EXISTS patient_profile JSONB;
                        ALTER TABLE chat_memories ADD COLUMN IF NOT EXISTS user_login VARCHAR(255);
                        """
                    )
            self._table_created = True
        except Exception as exc:
            self._logger.error("Erro ao garantir tabela chat_memories no PostgreSQL: %s", exc)

    def _base_memory(
        self,
        *,
        symptom_list: Optional[list[str]] = None,
        disease: Optional[str] = None,
        history: Optional[list[dict[str, Any]]] = None,
        patient_profile: Optional[dict] = None,
        user_login: Optional[str] = None,
    ) -> dict[str, Any]:
        return {
            "symptom_list": symptom_list or [],
            "disease": disease,
            "history": history or [],
            "patient_profile": patient_profile,
            "user_login": user_login,
        }

    async def get_memory(self, session_id: str) -> Optional[dict[str, Any]]:
        self._ensure_table()
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT disease, symptom_list, history, patient_profile, user_login FROM chat_memories WHERE session_id = %s",
                        (session_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None

                    disease = row[0]
                    symptom_list = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
                    history = row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]")
                    patient_profile = row[3] if isinstance(row[3], dict) else (
                        json.loads(row[3]) if row[3] else None
                    )
                    user_login = row[4]

                    return self._base_memory(
                        disease=disease,
                        symptom_list=symptom_list,
                        history=history,
                        patient_profile=patient_profile,
                        user_login=user_login,
                    )
        except Exception as exc:
            self._logger.error("Erro ao recuperar memória do PostgreSQL para %s: %s", session_id, exc)
            return None

    async def save_memory(
        self,
        session_id: str,
        symptom_list: list[str],
        disease: Optional[str],
        *,
        history: Optional[list[dict[str, Any]]] = None,
        patient_profile: Optional[dict] = None,
        user_login: Optional[str] = None,
    ) -> dict[str, Any]:
        data = self._base_memory(
            symptom_list=symptom_list,
            disease=disease,
            history=history,
            patient_profile=patient_profile,
            user_login=user_login,
        )
        return await self._write_data(session_id, data)

    async def append_history(self, session_id: str, role: str, message: str) -> dict[str, Any]:
        """
        Adiciona uma entrada (role/message) ao histórico da sessão no PostgreSQL.
        """
        data = await self.get_memory(session_id) or self._base_memory()

        history = data.get("history") or []
        history.append(
            {
                "role": role,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        if self._max_history_entries:
            history = history[-self._max_history_entries :]

        data["history"] = history
        return await self._write_data(session_id, data)

    async def _write_data(self, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
        self._ensure_table()
        try:
            disease = data.get("disease")
            symptom_list_json = json.dumps(data.get("symptom_list") or [])
            history_json = json.dumps(data.get("history") or [])
            profile_raw = data.get("patient_profile")
            profile_json = json.dumps(profile_raw) if profile_raw is not None else None
            user_login = data.get("user_login")

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO chat_memories (session_id, disease, symptom_list, history, patient_profile, user_login, updated_at)
                        VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s, NOW())
                        ON CONFLICT (session_id) DO UPDATE SET
                            disease = EXCLUDED.disease,
                            symptom_list = EXCLUDED.symptom_list,
                            history = EXCLUDED.history,
                            patient_profile = COALESCE(EXCLUDED.patient_profile, chat_memories.patient_profile),
                            user_login = COALESCE(EXCLUDED.user_login, chat_memories.user_login),
                            updated_at = NOW()
                        """,
                        (session_id, disease, symptom_list_json, history_json, profile_json, user_login),
                    )
        except Exception as exc:
            self._logger.error("Erro ao salvar memória no PostgreSQL para %s: %s", session_id, exc)

        return data
