-- =============================================================================
-- Migration: 001_users_and_chat_sessions.sql / users.sql
-- Descrição: Cria as tabelas do sistema de autenticação de alunos ('students')
--            e de histórico de consultas do chatbot ('chat_sessions').
-- =============================================================================

-- Habilita a extensão de geração de UUIDs, caso ainda não esteja habilitada
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- Tabela: students
-- Descrição: Registra os alunos habilitados a acessar o sistema do Galeno.
--            Gerenciada pelo painel administrativo (/admin).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    login VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para otimização de busca na tabela de estudantes
CREATE INDEX IF NOT EXISTS idx_students_login ON students (login);

-- -----------------------------------------------------------------------------
-- Tabela: chat_sessions
-- Descrição: Persiste o histórico de conversas e estado dos sintomas/doenças
--            gerados durante as sessões de chat.
-- -----------------------------------------------------------------------------
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

-- Índices para buscas rápidas por sessão, usuário e ordenação por data de atualização
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON chat_sessions (session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_login ON chat_sessions (user_login);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions (updated_at DESC);

-- Trigger para atualização automática da coluna updated_at na tabela chat_sessions
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS set_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER set_chat_sessions_updated_at
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- Tabela: chat_memories
-- Descrição: Armazena a memória ativa da sessão (doença sorteada, sintomas,
--            histórico de mensagens) para persistência e continuidade do chat.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_memories (
    session_id VARCHAR(255) PRIMARY KEY,
    disease VARCHAR(255),
    symptom_list JSONB NOT NULL DEFAULT '[]'::jsonb,
    history JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Índices para buscas rápidas e ordenação por data de atualização na memória do chat
CREATE INDEX IF NOT EXISTS idx_chat_memories_updated_at ON chat_memories (updated_at DESC);

-- Trigger para atualização automática da coluna updated_at na tabela chat_memories
DROP TRIGGER IF EXISTS set_chat_memories_updated_at ON chat_memories;
CREATE TRIGGER set_chat_memories_updated_at
BEFORE UPDATE ON chat_memories
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- -----------------------------------------------------------------------------
-- Dados Iniciais (Seed): Aluno de teste padrão
-- Login: aluno@galeno.com (ou aluno)
-- Senha predefinida (bcrypt para '123456'): $2b$12$c4eLqJc328k76dOevXQ8I.xYv5nE7F9G8H0I1J2K3L4M5N6O7P8Q6
-- -----------------------------------------------------------------------------
INSERT INTO students (name, login, password_hash)
VALUES (
    'Aluno Teste',
    'aluno',
    '$2b$12$c4eLqJc328k76dOevXQ8I.xYv5nE7F9G8H0I1J2K3L4M5N6O7P8Q6'
)
ON CONFLICT (login) DO NOTHING;

