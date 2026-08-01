from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.Api.chatController import router as chat_router
from src.Api.Admin.adminController import router as admin_router
from src.Api.Chat.chatSessionController import router as session_router


app = FastAPI(
    title="Galeno Chat API",
    version="1.0.0",
    description="API do simulador de consultas médicas Galeno",
)

# Em produção, troque ["*"] pelos domínios específicos do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(session_router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Healthcheck para verificar se a API está de pé."""
    return {"status": "ok"}
