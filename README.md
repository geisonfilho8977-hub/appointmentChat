# Galeno Chat — Backend

API backend do simulador de consultas médicas **Galeno**, construída com **FastAPI** + **LangChain** + **PostgreSQL**.

---

## Visão Geral

A API orquestra um sistema de múltiplos agentes de IA que simulam um paciente doente durante uma consulta virtual. O usuário assume o papel de médico e tenta diagnosticar a doença por meio de perguntas.

### Arquitetura de Agentes

```
Mensagem do Médico
        │
        ▼
   RouterAgent          ← classifica a intenção da mensagem
        │
        ├── sintomas    → SintomasAgent    (relata sintomas progressivamente)
        ├── conversation → ConversationAgent (mantém diálogo geral)
        ├── final       → FinalAgent       (encerra a consulta cordialmente)
        └── fallback    → FallbackAgent    (mensagens ininteligíveis)

Memória: LangChain + PostgreSQL (por session_id) ← histórico de conversa persistido
```

---

## Pré-requisitos

| Ferramenta | Versão mínima |
| ---------- | ------------- |
| Python     | 3.11+         |
| PostgreSQL | 14+           |
| pip / uv   | qualquer      |

---

## Instalação

```bash
# 1. Clone o repositório e entre na pasta
cd appointmentChat

# 2. Crie e ative um ambiente virtual
uv venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instale as dependências
uv sync
```

---

## Configuração do `.env`

Crie o arquivo `.env` na **raiz do projeto** (`appointmentChat/.env`):

```env
# ─── OpenAI ──────────────────────────────────
OPENAI_API_KEY=sk-...

# ─── Banco de dados ───────────────────────────
# Formato: postgresql://usuario:senha@host:porta/banco
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/galeno

# ─── Admin ────────────────────────────────────
# Chave secreta para acessar o painel /admin
ADMIN_SECRET_KEY=minha-chave-secreta-muito-forte

# ─── Google Gemini (opcional) ─────────────────
# GOOGLE_API_KEY=...
```

---

## Banco de Dados — Guia Completo (PostgreSQL no Linux)

### 1. Instalação do PostgreSQL

```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib

```

Verifique se está rodando:

```bash
sudo systemctl status postgresql
```

---

### 2. Acessar o psql como superusuário

O PostgreSQL cria o superusuário `postgres` durante a instalação. Acesse o terminal interativo do PostgreSQL:

```bash
sudo -u postgres psql
```

Você verá o prompt `postgres=#`.

---

### 3. Criar o banco de dados e definir a senha do superusuário

Dentro do `psql`, crie o banco de dados e defina a senha para o usuário `postgres` (substitua `'postgres'` pela senha que desejar):

```sql
-- Cria o banco de dados da aplicação
CREATE DATABASE galeno;

-- Define a senha do usuário postgres
ALTER USER postgres WITH PASSWORD 'postgres';

-- Sai do psql
\q
```

---

### 4. Testar a conexão

Você pode testar se a conexão com o banco de dados `galeno` usando o usuário `postgres` está funcionando:

```bash
sudo -u postgres psql -d galeno
# Ou informando usuário e host:
psql -h localhost -U postgres -d galeno
```

---

### 5. Montar a DATABASE_URL

O formato da URL de conexão do PostgreSQL para a aplicação é:

```
postgresql://postgres:<senha>@localhost:5432/galeno
```

Usando a senha definida no passo 3:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/galeno
```

Adicione essa linha ao seu arquivo `.env`.

---

### 6. Aplicar as migrações SQL

O projeto possui dois arquivos de migração na pasta `migrations/`:

| Arquivo           | O que cria                                                         |
| ----------------- | ------------------------------------------------------------------ |
| `appointment.sql` | Tabelas de doenças e sintomas (dados de simulação)                 |
| `users.sql`       | Tabelas de alunos (`students`) e sessões de chat (`chat_sessions`) |

Execute os dois scripts no banco `galeno` utilizando o usuário `postgres`:

```bash
# 1. Acesso ao diretório
cd migrations

# 2. Dados de pacientes e doenças
sudo -u postgres psql -d galeno -f appointment.sql

# 3. Usuários e sessões de chat
sudo -u postgres psql -d galeno -f users.sql
```

> **Alternativa (usando DATABASE_URL):**
>
> ```bash
> export DATABASE_URL=postgresql://postgres:minhasenha@localhost:5432/galeno
> psql $DATABASE_URL -f appointment.sql
> psql $DATABASE_URL -f users.sql
> ```

---

## Executando a API

```bash
# Desenvolvimento (com hot-reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Produção
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa: `http://localhost:8000/docs`

---

## Endpoints

### Chat

| Método | Endpoint     | Descrição                 |
| ------ | ------------ | ------------------------- |
| `POST` | `/chat/chat` | Envia mensagem ao chatbot |

**Body:**

```json
{
  "session_id": "uuid-da-sessão",
  "message": "Bom dia, doutor!"
}
```

### Sessões de Chat (persistência)

| Método   | Endpoint                          | Descrição                     |
| -------- | --------------------------------- | ----------------------------- |
| `GET`    | `/chat/sessions/{session_id}`     | Lista chats salvos da sessão  |
| `GET`    | `/chat/sessions/detail/{chat_id}` | Recupera um chat pelo ID      |
| `POST`   | `/chat/sessions`                  | Salva a sessão atual no banco |
| `DELETE` | `/chat/sessions/{chat_id}`        | Deleta um chat salvo          |

### Admin (protegido por `X-Admin-Key`)

| Método   | Endpoint               | Descrição                    |
| -------- | ---------------------- | ---------------------------- |
| `GET`    | `/admin/verify`        | Verifica se a chave é válida |
| `GET`    | `/admin/students`      | Lista alunos cadastrados     |
| `POST`   | `/admin/students`      | Cadastra novo aluno          |
| `DELETE` | `/admin/students/{id}` | Remove aluno                 |

Todos os endpoints admin exigem o header:

```
X-Admin-Key: <ADMIN_SECRET_KEY>
```

### Health

| Método | Endpoint  | Descrição   |
| ------ | --------- | ----------- |
| `GET`  | `/health` | Healthcheck |

---

## Estrutura do Projeto

```
appointmentChat/
├── app.py                          # FastAPI app — registra routers
├── pyproject.toml                  # Dependências
├── migrations/
│   └── 001_add_students_and_chat_sessions.sql
└── src/
    ├── Api/
    │   ├── chatController.py       # POST /chat/chat
    │   ├── Admin/
    │   │   └── adminController.py  # /admin/*
    │   └── Chat/
    │       └── chatSessionController.py  # /chat/sessions/*
    ├── Application/
    │   └── Handlers/Chat/
    │       └── ChatCommandHandler.py  # Orquestrador de agentes
    ├── Domain/
    │   ├── Chatbot/
    │   │   ├── Abstractions/AgentInterface.py
    │   │   └── Agents/
    │   │       ├── RouterAgent/      # Classifica intenção
    │   │       ├── SintomasAgent/    # Relata sintomas
    │   │       ├── ConversationAgent/ # Diálogo geral
    │   │       ├── FinalAgent/       # Encerramento
    │   │       └── FallBackAgent/    # Fallback
    │   ├── Entities/                 # Patient, Symptom
    │   ├── Factories/AgentFactory.py
    │   └── Interfaces/Llm/
    ├── Infrastructure/
    │   ├── Cache/
    │   │   ├── ChatMemoryStore.py    # Redis — memória de sessão
    │   │   └── LangChainMemoryAdapter.py
    │   ├── Database/
    │   │   ├── Config.py             # DATABASE_URL
    │   │   └── Connection.py         # Pool psycopg
    │   ├── Llm/
    │   │   ├── LangChainOpenAILlm.py # Provider principal (async)
    │   │   └── DefaultLlmProviderResolver.py
    │   └── Repositories/
    │       ├── PatientRepositoryPstgres.py
    │       ├── PatientSymptomRepositoryPostgres.py
    │       ├── StudentRepositoryPostgres.py
    │       └── ChatSessionRepositoryPostgres.py
    └── SharedKernel/
        ├── Logging/
        ├── Messages/
        └── Observer/
```

---

## Variáveis de Ambiente — Referência Rápida

| Variável           | Obrigatória | Descrição                     |
| ------------------ | ----------- | ----------------------------- |
| `OPENAI_API_KEY`   | ✅          | Chave da API OpenAI           |
| `DATABASE_URL`     | ✅          | Connection string PostgreSQL  |
| `ADMIN_SECRET_KEY` | ✅          | Chave do painel admin         |
| `GOOGLE_API_KEY`   | ❌          | Para uso do Gemini (opcional) |

---

## Dicas de Desenvolvimento

- **Logs coloridos**: configurados via `colorama` — você verá o roteamento de agentes no terminal.
- **Hot-reload**: use `--reload` no uvicorn para desenvolvimento.
- **Docs interativas**: acesse `/docs` (Swagger UI) ou `/redoc` para explorar a API.
- **Redis obrigatório**: a memória de sessão usa Redis. Certifique-se de que ele está rodando antes de iniciar a API.
