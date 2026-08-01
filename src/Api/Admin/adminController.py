"""
Controller do painel administrativo + autenticação de alunos.

Endpoints admin (protegidos por X-Admin-Key):
  GET  /admin/verify          — verifica chave
  GET  /admin/students        — lista alunos
  POST /admin/students        — cadastra aluno (nome, login, senha)
  DELETE /admin/students/{id} — remove aluno

Endpoint público de login (usado pelo frontend):
  POST /admin/login           — autentica aluno, retorna token de sessão simples
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from fastapi import APIRouter, Header, HTTPException, status, Depends
from pydantic import BaseModel

from src.Infrastructure.Repositories.StudentRepositoryPostgres import (
    StudentRepositoryPostgres,
    Student,
)
from src.SharedKernel.Logging.Logger import get_logger


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_admin_key() -> str:
    key = os.getenv("ADMIN_SECRET_KEY")
    if not key:
        env_path = Path(__file__).resolve().parents[3] / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
            key = os.getenv("ADMIN_SECRET_KEY")
    if not key:
        raise RuntimeError("ADMIN_SECRET_KEY não configurada no ambiente")
    return key


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/admin", tags=["Admin"])
_logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Auth dependency (admin)
# ---------------------------------------------------------------------------

def verify_admin_key(x_admin_key: str = Header(..., alias="X-Admin-Key")) -> None:
    """Valida o header X-Admin-Key contra ADMIN_SECRET_KEY do .env."""
    expected = _get_admin_key()
    if x_admin_key != expected:
        _logger.warning("Tentativa de acesso admin com chave inválida")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave administrativa inválida.",
        )


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

class StudentOut(BaseModel):
    id: str
    name: str
    login: str
    created_at: str

    @classmethod
    def from_model(cls, s: Student) -> "StudentOut":
        return cls(
            id=str(s.id),
            name=s.name,
            login=s.login,
            created_at=s.created_at.isoformat(),
        )


class CreateStudentIn(BaseModel):
    name: str
    login: str
    password: str


class LoginIn(BaseModel):
    login: str
    password: str


class LoginOut(BaseModel):
    ok: bool
    name: str
    login: str


# ---------------------------------------------------------------------------
# Endpoints — Admin (protegidos)
# ---------------------------------------------------------------------------

@router.get(
    "/verify",
    summary="Verifica se a chave admin é válida",
    dependencies=[Depends(verify_admin_key)],
)
def verify_key() -> dict:
    return {"ok": True}


@router.get(
    "/students",
    summary="Lista todos os alunos cadastrados",
    response_model=List[StudentOut],
    dependencies=[Depends(verify_admin_key)],
)
def list_students() -> List[StudentOut]:
    repo = StudentRepositoryPostgres()
    students = repo.list_all()
    return [StudentOut.from_model(s) for s in students]


@router.post(
    "/students",
    summary="Cadastra um novo aluno com login e senha",
    response_model=StudentOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_key)],
)
def create_student(body: CreateStudentIn) -> StudentOut:
    repo = StudentRepositoryPostgres()

    # Verifica duplicata de login
    existing = repo.get_by_login(body.login)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Login '{body.login}' já cadastrado.",
        )

    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A senha deve ter no mínimo 6 caracteres.",
        )

    student = repo.create(
        name=body.name.strip(),
        login=body.login.strip(),
        password=body.password,
    )
    return StudentOut.from_model(student)


@router.delete(
    "/students/{student_id}",
    summary="Remove um aluno pelo ID",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_admin_key)],
)
def delete_student(student_id: str) -> dict:
    repo = StudentRepositoryPostgres()
    deleted = repo.delete(student_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado.",
        )
    return {"ok": True, "deleted_id": student_id}


# ---------------------------------------------------------------------------
# Endpoint público — Login de aluno
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    summary="Autentica um aluno (login + senha)",
    response_model=LoginOut,
)
def student_login(body: LoginIn) -> LoginOut:
    """
    Valida credenciais do aluno. Retorna dados do usuário se válidas.
    O frontend armazena o login em sessionStorage para controlar acesso ao chat.
    """
    repo = StudentRepositoryPostgres()
    student = repo.verify_password(login=body.login, password=body.password)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login ou senha incorretos.",
        )

    _logger.info(f"Login bem-sucedido: {student.login}")
    return LoginOut(ok=True, name=student.name, login=student.login)
