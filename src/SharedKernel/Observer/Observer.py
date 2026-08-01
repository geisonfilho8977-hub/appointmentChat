from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class Observer(ABC):
    """Interface base para observadores."""
    
    @abstractmethod
    def update(self, message: Dict[str, Any]) -> None:
        """
        Método chamado quando uma nova mensagem é processada.
        
        Args:
            message: Dicionário contendo informações da mensagem
        """
        pass

class MessageSubject:
    """Classe que mantém e notifica os observadores sobre novas mensagens."""
    
    def __init__(self):
        self._observers: List[Observer] = []
        
    def attach(self, observer: Observer) -> None:
        """Adiciona um novo observador."""
        if observer not in self._observers:
            self._observers.append(observer)
            
    def detach(self, observer: Observer) -> None:
        """Remove um observador."""
        self._observers.remove(observer)
        
    def notify(self, message: str, role: str) -> None:
        """
        Notifica todos os observadores sobre uma nova mensagem.
        
        Args:
            message: Conteúdo da mensagem
            role: Papel do emissor (user/assistant)
        """
        message_info = {
            "content": message,
            "role": role,
            "timestamp": datetime.now().isoformat()
        }
        
        for observer in self._observers:
            observer.update(message_info)

class LoggingObserver(Observer):
    """Observador que registra mensagens no log."""
    
    def __init__(self, logger):
        self.logger = logger
        
    def update(self, message: Dict[str, Any]) -> None:
        role_emoji = "👤" if message["role"] == "user" else "🤖"
        self.logger.info(f"{role_emoji} {message['content']}") 