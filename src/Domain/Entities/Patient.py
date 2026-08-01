from uuid import UUID
from typing import Optional


class Patient:
    def __init__(self, patient_id: UUID, disease: Optional[str] = None):
        self.patient_id = patient_id
        self.disease = disease



