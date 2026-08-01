"""
Repositório de estudantes (alunos) no PostgreSQL.
Gerenciado pelo painel admin — suporta CRUD completo.

Campos:
  - login: identificador único do usuário (pode ser e-mail ou qualquer string)
  - password_hash: hash bcrypt da senha
"""
from __future__ import annotations

import bcrypt
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.Infrastructure.Database.Connection import get_connection
from src.SharedKernel.Logging.Logger import get_logger


@dataclass
class Student:
    id: UUID
    name: str
    login: str
    created_at: datetime


class StudentRepositoryPostgres:
    def __init__(self):
        self._logger = get_logger(__name__)

    # ─── Leitura ─────────────────────────────────────────────────────────────

    def list_all(self) -> List[Student]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, login, created_at FROM students ORDER BY created_at DESC"
                )
                rows = cur.fetchall()
                return [Student(id=r[0], name=r[1], login=r[2], created_at=r[3]) for r in rows]

    def get_by_login(self, login: str) -> Optional[Student]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, login, created_at FROM students WHERE login = %s",
                    (login.strip().lower(),),
                )
                row = cur.fetchone()
                return Student(id=row[0], name=row[1], login=row[2], created_at=row[3]) if row else None

    # ─── Autenticação ─────────────────────────────────────────────────────────

    def verify_password(self, login: str, password: str) -> Optional[Student]:
        """
        Verifica credenciais. Retorna o Student se válidas, None caso contrário.
        Usa hash bcrypt — seguro contra timing attacks.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, login, password_hash, created_at FROM students WHERE login = %s",
                    (login.strip().lower(),),
                )
                row = cur.fetchone()
                if not row:
                    return None

                stored_hash = row[3]
                password_bytes = password.encode("utf-8")
                hash_bytes = stored_hash.encode("utf-8") if isinstance(stored_hash, str) else stored_hash

                if not bcrypt.checkpw(password_bytes, hash_bytes):
                    return None

                return Student(id=row[0], name=row[1], login=row[2], created_at=row[4])

    # ─── Escrita ──────────────────────────────────────────────────────────────

    def create(self, name: str, login: str, password: str) -> Student:
        """Cria um aluno com senha hasheada (bcrypt)."""
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO students (name, login, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, login, created_at
                    """,
                    (name.strip(), login.strip().lower(), password_hash),
                )
                row = cur.fetchone()
                self._logger.info(f"Aluno cadastrado: {login}")
                return Student(id=row[0], name=row[1], login=row[2], created_at=row[3])

    def delete(self, student_id: str) -> bool:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM students WHERE id = %s RETURNING id",
                    (student_id,),
                )
                deleted = cur.fetchone()
                if deleted:
                    self._logger.info(f"Aluno removido: {student_id}")
                return deleted is not None
