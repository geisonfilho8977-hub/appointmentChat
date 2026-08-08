# Galeno Chat — Backend

API backend do simulador de consultas médicas **Galeno**, construída com **FastAPI** + **LangChain** + **PostgreSQL** + **OpenAI GPT-4o-mini**.

---

## 🌟 Visão Geral

A API orquestra um sistema de múltiplos agentes de IA que simulam um paciente doente durante uma consulta virtual de anamnese. O estudante de medicina assume o papel de médico e tenta diagnosticar a doença por meio de perguntas clínicas.

### 🎭 Perfil Comportamental do Paciente
Cada nova consulta sorteia aleatoriamente um **perfil comportamental em 5 dimensões**, garantindo alta diversidade e realismo:
1. **Grau de Cooperação**: Alto, Moderado, Baixo.
2. **Organização do Discurso**: Organizado, Circunstancial, Tangencial, Desorganizado.
3. **Expressividade Emocional**: Neutro, Ansioso, Dramático, Apático.
4. **Controle de Informação**: Espontâneo, Econômico, Reticente, Verborrágico.
5. **Atitude com o Médico**: Colaborativo, Desconfiado, Hostil, Dependente.

Além das 5 dimensões, cada paciente possui um **contexto de vida** (ocupação, rotina e família) sorteado aleatoriamente, com diretivas estritas de anti-repetição verbal e empatia adaptativa.

### 🤖 Arquitetura de Agentes

```
Mensagem do Médico
        │
        ▼
   RouterAgent          ← Classifica a intenção (temperature=0.0)
        │
        ├── sintomas     → SintomasAgent    (relata sintomas de forma gradual)
        ├── conversation → ConversationAgent (mantém diálogo e interação)
        ├── final        → FinalAgent       (encerra a consulta cordialmente)
        └── fallback     → FallbackAgent    (reorienta mensagens ininteligíveis)

Memória: LangChain + PostgreSQL (chat_memories) ← histórico e perfil persistidos por session_id
Tokens: Computados em tempo real na tabela `students` a cada interação
```

---

## 🛠️ Pré-requisitos

| Ferramenta | Versão mínima |
| ---------- | ------------- |
| Python     | 3.11+         |
| PostgreSQL | 14+           |
| Docker     | 20+ (opcional)|

---

## ⚡ Instalação e Execução Local

```bash
# 1. Entre na pasta do backend
cd appointmentChat

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis no .env
cp .env.example .env

# 5. Inicie o servidor
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

---

## 📝 Variáveis de Ambiente (`.env`)

```env
# ─── OpenAI ──────────────────────────────────
OPENAI_API_KEY=sk-proj-sua_chave_openai_aqui

# ─── Banco de Dados ───────────────────────────
DATABASE_URL=postgresql://usuario:senha@localhost:5432/galeno_db

# ─── Admin ────────────────────────────────────
ADMIN_SECRET_KEY=sua_chave_secreta_admin
```

---

## 📊 Estrutura do Projeto

```
appointmentChat/
├── app.py                      # Ponto de entrada FastAPI
├── Dockerfile                  # Containerização do Backend
├── entrypoint.sh               # Script de inicialização do container
├── requirements.txt            # Dependências Python
└── src/
    ├── Api/                    # Controllers (chatController, adminController, chatSessionController)
    ├── Application/            # Handlers e DTOs (ChatCommandHandler)
    ├── Domain/                 # Agentes, Prompts e Entidades (PatientProfile, ProfilePromptBuilder)
    ├── Infrastructure/         # Repositórios PostgreSQL, Cache e Resolver LLM (LangChainOpenAILlm)
    └── SharedKernel/           # Logs, Observers e Exceções
```

---

## 🐳 Conteinerização com Docker & Ngrok

O backend está pronto para rodar conteinerizado via `docker-compose.yml` na raiz do projeto, integrando PostgreSQL, Backend, Frontend e túnel público seguro **Ngrok**..
