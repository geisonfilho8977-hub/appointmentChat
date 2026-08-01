"""
Controller principal do chat.

Usa FastAPI Dependency Injection para garantir que ChatCommandHandler
seja um singleton por aplicação (evita perda de estado entre requests).
"""
from fastapi import APIRouter, Depends
from src.Application.Handlers.Chat.DTOs_.ChatCommand import ChatCommand
from src.Application.Handlers.Chat.ChatCommandHandler import ChatCommandHandler

router = APIRouter(prefix="/chat", tags=["Chat"])

# Instância singleton do handler — compartilhada entre todos os requests
_handler_instance: ChatCommandHandler | None = None


def get_chat_handler() -> ChatCommandHandler:
    """
    FastAPI dependency que retorna sempre a mesma instância do ChatCommandHandler.
    Isso garante que o AgentFactory e os repositórios sejam inicializados apenas
    uma vez, evitando overhead desnecessário a cada request.
    """
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = ChatCommandHandler()
    return _handler_instance


@router.post("/chat", summary="Envia mensagem ao chatbot")
async def send_message(
    command: ChatCommand,
    handler: ChatCommandHandler = Depends(get_chat_handler),
):
    result = await handler.handle(command)
    return {"message": result}
