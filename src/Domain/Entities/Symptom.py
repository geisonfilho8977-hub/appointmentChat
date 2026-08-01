from uuid import UUID


class Symptom:
    def __init__(self, symptom_id: UUID, symptom_name: str):
        self.symptom_id = symptom_id
        self.symptom_name = symptom_name


