from uuid import UUID


class PatientSymptom:
    def __init__(self, patient_id: UUID, symptom_id: UUID):
        self.patient_id = patient_id
        self.symptom_id = symptom_id


