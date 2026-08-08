from typing import List, Optional
from uuid import UUID

from src.Domain.Entities.Patient import Patient
from src.Infrastructure.Database.Connection import get_connection
from src.Domain.Interfaces.Repositories.PatientRepository import PatientRepository


class PatientRepositoryPostgres(PatientRepository):
    def __init__(self):
        self.connection = get_connection()
    
    def get_patient(self, id: str) -> Patient:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "patient_id", disease FROM patients WHERE "patient_id" = %s',
                    (id,),
                )
                row = cur.fetchone()
                if not row:
                    raise ValueError(f"Patient with id {id} not found")
                return Patient(patient_id=row[0], disease=row[1])
    
    def get_by_id(self, patient_id: UUID) -> Optional[Patient]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT "patient_id", disease FROM patients WHERE "patient_id" = %s',
                    (str(patient_id),),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return Patient(patient_id=row[0], disease=row[1])

    def list_all(self) -> List[Patient]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT "patient_id", disease FROM patients ORDER BY "patient_id"')
                rows = cur.fetchall()
                return [Patient(patient_id=r[0], disease=r[1]) for r in rows]


