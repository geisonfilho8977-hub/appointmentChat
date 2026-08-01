from fastapi import APIRouter
from src.Application.Handlers.Chat.DTOs_.ChatCommand import ChatCommand
from src.Application.Handlers.Chat.ChatCommandHandler import ChatCommandHandler

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/chat")
async def send_message(command: ChatCommand):
    chat_command_handler = ChatCommandHandler()
    result = await chat_command_handler.handle(command)
    return {"message": result}
