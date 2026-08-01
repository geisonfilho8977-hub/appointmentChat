from abc import ABC
from abc import abstractmethod
from src.Domain.Entities.Patient import Patient


class PatientRepository(ABC):
    @abstractmethod
    def get_patient(self, id: str) -> Patient:
        pass