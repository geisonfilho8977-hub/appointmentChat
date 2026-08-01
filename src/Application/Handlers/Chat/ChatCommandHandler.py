from typing import Any, List, Optional, Tuple
import random

from src.Domain.Chatbot.Abstractions.AgentInterface import (
    AgentInterface,
    AgentType,
    AgentResponse,
)
from src.Domain.Factories.AgentFactory import AgentFactory
from src.Infrastructure.Llm.DefaultLlmProviderResolver import DefaultLlmProviderResolver
from src.SharedKernel.Messages.Exceptions import (
    HandlerNotFoundError,
    MessageProcessingError,
    AgentConfigurationError,
    AgentTypeNotFoundError,
)
from src.SharedKernel.Logging.Logger import get_logger
from src.SharedKernel.Observer.Observer import MessageSubject, LoggingObserver
from src.Application.Handlers.Chat.DTOs_.ChatCommand import ChatCommand

from src.Infrastructure.Repositories.PatientRepositoryPstgres import PatientRepositoryPostgres
from src.Infrastructure.Repositories.PatientSymptomRepositoryPostgres import PatientSymptomRepositoryPostgres
from src.Domain.Entities.Symptom import Symptom
from src.Infrastructure.Cache.ChatMemoryStore import ChatMemoryStore


class ChatCommandHandler:
    """
    Orquestra o fluxo de mensagens entre os agentes.

    Gerencia:
    - Inicialização e roteamento entre agentes (Router → Sintomas/Conversation/Final/Fallback)
    - Persistência do histórico no PostgreSQL via ChatMemoryStore (gerenciado via LangChain)
    - Seleção aleatória de paciente/doença ao iniciar nova sessão
    """

    HISTORY_WINDOW = 500  # Número máximo de mensagens passadas enviadas ao prompt

    def __init__(self, agent_factory: Optional[AgentFactory] = None):
        self.logger = get_logger(__name__)
        self.agent_factory = agent_factory or AgentFactory(
            llm_provider_resolver=DefaultLlmProviderResolver()
        )

        self.message_subject = MessageSubject()
        self.message_subject.attach(LoggingObserver(self.logger))

        self.patient_repository = PatientRepositoryPostgres()
        self.patient_symptom_repository = PatientSymptomRepositoryPostgres()
        self.chat_memory_store = ChatMemoryStore()

        self.logger.info("💬 ChatCommandHandler inicializado")

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------

    async def handle(self, command: ChatCommand) -> str:
        session_id = str(command.session_id)
        message = command.message

        # Garante que a sessão existe no Redis (cria com dados aleatórios se nova)
        memory = await self._ensure_session_memory(session_id)

        # Salva mensagem do usuário no histórico
        memory = await self.chat_memory_store.append_history(session_id, "user", message)

        self.message_subject.notify(message=message, role="user")

        # Extrai contexto da sessão
        symptom_list = memory.get("symptom_list") or []
        disease = memory.get("disease")
        history = memory.get("history") or []
        conversation_context = self._format_history(history)

        # Loop de roteamento: começa no router, vai ao agente adequado
        current_agent_type = "router"

        while True:
            prompt_data = self._build_prompt_data(
                agent_type=current_agent_type,
                conversation_context=conversation_context,
                symptom_list=symptom_list,
                disease=disease,
            )

            agent = self._get_agent(
                agent_type=current_agent_type,
                llm_type="gpt",
                prompt_data=prompt_data,
            )

            response: AgentResponse = await agent.generate_response(message)

            if response.message:
                self.message_subject.notify(message=response.message, role="assistant")
                memory = await self.chat_memory_store.append_history(
                    session_id, "assistant", response.message
                )
                history = memory.get("history") or []
                conversation_context = self._format_history(history)

            if response.agent_type == AgentType.FINAL:
                return response.message or ""

            # Resolve próximo agente com fallback seguro
            next_agent = response.next_agent or "sintomas"
            if next_agent not in self.agent_factory.agent_classes:
                self.logger.warning(
                    f"Agente '{next_agent}' inválido — usando 'sintomas' como fallback"
                )
                next_agent = "sintomas"

            self.logger.info(f"🔀 Roteando para agente '{next_agent}'")
            current_agent_type = next_agent

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _get_agent(self, agent_type: str, llm_type: str, prompt_data: dict) -> AgentInterface:
        try:
            return self.agent_factory.create_agent(
                agent_type=agent_type,
                llm_type=llm_type,
                prompt_data=prompt_data,
            )
        except (HandlerNotFoundError, AgentConfigurationError, AgentTypeNotFoundError):
            raise
        except ValueError as e:
            raise AgentConfigurationError(f"Erro de configuração: {e}")
        except Exception as e:
            raise HandlerNotFoundError(f"Erro ao criar agente: {e}")

    async def _ensure_session_memory(self, session_id: str) -> dict[str, Any]:
        """Retorna a memória existente ou cria uma nova sessão com paciente aleatório."""
        existing = await self.chat_memory_store.get_memory(session_id)
        if existing:
            return existing

        symptom_entities, disease = self._get_random_patient_data()
        symptom_list = [s.symptom_name for s in symptom_entities]

        return await self.chat_memory_store.save_memory(
            session_id=session_id,
            symptom_list=symptom_list,
            disease=disease,
        )

    def _get_random_patient_data(self) -> Tuple[List[Symptom], Optional[str]]:
        all_patients = self.patient_repository.list_all()
        if not all_patients:
            self.logger.warning("Nenhum paciente encontrado no banco")
            return [], None

        patient = random.choice(all_patients)
        symptoms = self.patient_symptom_repository.list_symptoms_for_patient(patient.patient_id)
        self.logger.info(f"Paciente sorteado: {patient.patient_id} | Doença: {patient.disease}")
        return symptoms, patient.disease

    def _format_history(self, history: list) -> str:
        """Formata as últimas N mensagens do histórico para injeção no prompt."""
        if not history:
            return ""
        relevant = history[-self.HISTORY_WINDOW:]
        lines = []
        for entry in relevant:
            role = (entry.get("role") or "user").upper()
            content = entry.get("message") or ""
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _build_prompt_data(
        self,
        agent_type: str,
        conversation_context: str,
        symptom_list: list,
        disease: Optional[str],
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"conversation_history": conversation_context}
        if agent_type == "sintomas":
            data["symptom_list"] = symptom_list
            data["disease"] = disease
        return data
