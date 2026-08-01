class POOChatException(Exception):
    """Exceção base para todas as exceções do POO Chat."""
    pass

class HandlerNotFoundError(POOChatException):
    """Exceção lançada quando um handler não é encontrado."""
    pass

class AgentTypeNotFoundError(POOChatException):
    """Exceção lançada quando uma configuração de agente não é encontrada."""
    pass

class AgentConfigurationError(POOChatException):
    """Exceção lançada quando há erro na configuração de um agente."""
    pass

class MessageProcessingError(POOChatException):
    """Exceção lançada quando há erro no processamento de mensagens."""
    pass

class OpenAIError(POOChatException):
    """Exceção lançada quando há erro na comunicação com a OpenAI."""
    pass 