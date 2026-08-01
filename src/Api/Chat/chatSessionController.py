"""
Controller de sessões de chat (históricos persistidos).

Permite salvar, listar, recuperar e deletar chats
para que o usuário possa revisitar consultas anteriores.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.Infrastructure.Repositories.ChatSessionRepositoryPostgres import (
    ChatSessionRepositoryPostgres,
    ChatSession,
)
from src.Infrastructure.Cache.ChatMemoryStore import ChatMemoryStore
from src.SharedKernel.Logging.Logger import get_logger


router = APIRouter(prefix="/chat/sessions", tags=["Chat Sessions"])
_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class ChatSessionOut(BaseModel):
    id: str
    session_id: str
    title: str
    disease: Optional[str]
    symptom_list: List[str]
    history: List[Dict[str, Any]]
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, s: ChatSession) -> "ChatSessionOut":
        return cls(
            id=str(s.id),
            session_id=s.session_id,
            title=s.title,
            disease=s.disease,
            symptom_list=s.symptom_list,
            history=s.history,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )


class SaveSessionIn(BaseModel):
    session_id: str
    title: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/{session_id}",
    summary="Lista chats salvos de uma sessão",
    response_model=List[ChatSessionOut],
)
def list_sessions(session_id: str) -> List[ChatSessionOut]:
    repo = ChatSessionRepositoryPostgres()
    sessions = repo.list_by_session(session_id)
    return [ChatSessionOut.from_model(s) for s in sessions]


@router.get(
    "/detail/{chat_id}",
    summary="Recupera um chat salvo pelo ID",
    response_model=ChatSessionOut,
)
def get_session(chat_id: str) -> ChatSessionOut:
    repo = ChatSessionRepositoryPostgres()
    session = repo.get_by_id(chat_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")
    return ChatSessionOut.from_model(session)


@router.post(
    "",
    summary="Salva o chat atual no banco",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def save_session(body: SaveSessionIn) -> ChatSessionOut:
    """
    Salva o histórico ativo da sessão no PostgreSQL para consultas permanentes.
    O título é gerado automaticamente a partir da primeira mensagem se não informado.
    """
    store = ChatMemoryStore()
    memory = await store.get_memory(body.session_id)

    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma memória encontrada para essa sessão.",
        )

    history = memory.get("history") or []
    disease = memory.get("disease")
    symptom_list = memory.get("symptom_list") or []

    # Gerar título automático a partir da primeira mensagem do usuário
    title = body.title
    if not title:
        first_user = next(
            (h.get("message", "") for h in history if h.get("role") == "user"), ""
        )
        title = first_user[:60] + ("..." if len(first_user) > 60 else "") if first_user else "Consulta"

    repo = ChatSessionRepositoryPostgres()
    session = repo.save(
        session_id=body.session_id,
        title=title,
        history=history,
        disease=disease,
        symptom_list=symptom_list,
    )
    return ChatSessionOut.from_model(session)


@router.delete(
    "/{chat_id}",
    summary="Deleta um chat salvo",
    status_code=status.HTTP_200_OK,
)
def delete_session(chat_id: str) -> dict:
    repo = ChatSessionRepositoryPostgres()
    deleted = repo.delete(chat_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")
    return {"ok": True, "deleted_id": chat_id}
