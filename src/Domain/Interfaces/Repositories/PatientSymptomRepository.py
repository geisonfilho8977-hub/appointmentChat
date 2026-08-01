from abc import ABC
from abc import abstractmethod
from src.Domain.Entities.PatientSymptom import PatientSymptom


class PatientSymptomRepository(ABC):
    @abstractmethod
    def get_patient_symptoms(self, id: str) -> list[PatientSymptom]:
        pass