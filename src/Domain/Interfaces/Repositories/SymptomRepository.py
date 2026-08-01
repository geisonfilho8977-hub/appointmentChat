from abc import ABC
from abc import abstractmethod
from src.Domain.Entities.Symptom import Symptom


class SymptomRepository(ABC):
    @abstractmethod
    def get_symptom(self, id: str) -> Symptom:
        pass