from typing import List
from uuid import UUID

from src.Domain.Entities.Patient import Patient
from src.Domain.Entities.Symptom import Symptom
from src.Domain.Entities.PatientSymptom import PatientSymptom
from src.Infrastructure.Database.Connection import get_connection
from src.Domain.Interfaces.Repositories.PatientSymptomRepository import PatientSymptomRepository


class PatientSymptomRepositoryPostgres(PatientSymptomRepository):
    def __init__(self):
        pass

    def get_patient_symptoms(self, id: str) -> list[PatientSymptom]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "patient_id", "symptom_id" FROM patient_symptoms WHERE "patient_id" = %s',
                    (id,),
                )
                rows = cur.fetchall()
                return [PatientSymptom(patient_id=r[0], symptom_id=r[1]) for r in rows]

    def list_symptoms_for_patient(self, patient_id: UUID) -> List[Symptom]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT s."symptom_id", s."symptom_name" 
                       FROM symptoms s
                       INNER JOIN patient_symptoms ps ON s."symptom_id" = ps."symptom_id"
                       WHERE ps."patient_id" = %s''',
                    (str(patient_id),),
                )
                rows = cur.fetchall()
                return [Symptom(symptom_id=r[0], symptom_name=r[1]) for r in rows]

    def list_patients_for_symptom(self, symptom_id: UUID) -> List[Patient]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''SELECT p."patient_id", p."disease" 
                       FROM patients p
                       INNER JOIN patient_symptoms ps ON p."patient_id" = ps."patient_id"
                       WHERE ps."symptom_id" = %s''',
                    (str(symptom_id),),
                )
                rows = cur.fetchall()
                return [Patient(patient_id=r[0], disease=r[1]) for r in rows]


