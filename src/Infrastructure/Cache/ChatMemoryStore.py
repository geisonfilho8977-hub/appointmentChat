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

    def _base_memory(
        self,
        *,
        symptom_list: Optional[list[str]] = None,
        disease: Optional[str] = None,
        history: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        return {
            "symptom_list": symptom_list or [],
            "disease": disease,
            "history": history or [],
        }

    async def get_memory(self, session_id: str) -> Optional[dict[str, Any]]:
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT disease, symptom_list, history FROM chat_memories WHERE session_id = %s",
                        (session_id,),
                    )
                    row = cur.fetchone()
                    if not row:
                        return None

                    disease = row[0]
                    symptom_list = row[1] if isinstance(row[1], list) else json.loads(row[1] or "[]")
                    history = row[2] if isinstance(row[2], list) else json.loads(row[2] or "[]")

                    return self._base_memory(
                        disease=disease,
                        symptom_list=symptom_list,
                        history=history,
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
    ) -> dict[str, Any]:
        data = self._base_memory(
            symptom_list=symptom_list,
            disease=disease,
            history=history,
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
        try:
            disease = data.get("disease")
            symptom_list_json = json.dumps(data.get("symptom_list") or [])
            history_json = json.dumps(data.get("history") or [])

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO chat_memories (session_id, disease, symptom_list, history, updated_at)
                        VALUES (%s, %s, %s::jsonb, %s::jsonb, NOW())
                        ON CONFLICT (session_id) DO UPDATE SET
                            disease = EXCLUDED.disease,
                            symptom_list = EXCLUDED.symptom_list,
                            history = EXCLUDED.history,
                            updated_at = NOW()
                        """,
                        (session_id, disease, symptom_list_json, history_json),
                    )
        except Exception as exc:
            self._logger.error("Erro ao salvar memória no PostgreSQL para %s: %s", session_id, exc)

        return data
