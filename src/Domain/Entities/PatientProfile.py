"""
Entidade de domínio que representa o perfil comportamental de um paciente simulado.

Cinco dimensões são sorteadas aleatoriamente a cada nova sessão e persistem
ao longo de toda a conversa, garantindo consistência de personagem.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


# ─── Opções por dimensão ──────────────────────────────────────────────────────

COOPERATION_LEVELS  = ["alto", "moderado", "baixo"]
DISCOURSE_STYLES    = ["organizado", "circunstancial", "tangencial", "desorganizado"]
EMOTIONALITY_TYPES  = ["neutro", "ansioso", "dramatico", "apatico"]
INFO_CONTROL_TYPES  = ["espontaneo", "economico", "reticente", "verborrágico"]
ATTITUDE_TYPES      = ["colaborativo", "desconfiado", "hostil", "dependente"]


# ─── Entidade ─────────────────────────────────────────────────────────────────

@dataclass
class PatientProfile:
    """Perfil comportamental do paciente com 5 dimensões."""

    cooperation: str   # "alto" | "moderado" | "baixo"
    discourse: str     # "organizado" | "circunstancial" | "tangencial" | "desorganizado"
    emotionality: str  # "neutro" | "ansioso" | "dramatico" | "apatico"
    info_control: str  # "espontaneo" | "economico" | "reticente" | "verborrágico"
    attitude: str      # "colaborativo" | "desconfiado" | "hostil" | "dependente"

    @staticmethod
    def random() -> "PatientProfile":
        """Gera um perfil aleatório sorteando 1 valor por dimensão."""
        return PatientProfile(
            cooperation=random.choice(COOPERATION_LEVELS),
            discourse=random.choice(DISCOURSE_STYLES),
            emotionality=random.choice(EMOTIONALITY_TYPES),
            info_control=random.choice(INFO_CONTROL_TYPES),
            attitude=random.choice(ATTITUDE_TYPES),
        )

    @staticmethod
    def from_dict(d: dict) -> "PatientProfile":
        """Reconstrói o perfil a partir de um dicionário (armazenado no banco)."""
        return PatientProfile(
            cooperation=d.get("cooperation", "moderado"),
            discourse=d.get("discourse", "organizado"),
            emotionality=d.get("emotionality", "neutro"),
            info_control=d.get("info_control", "economico"),
            attitude=d.get("attitude", "colaborativo"),
        )

    def to_dict(self) -> dict:
        """Serializa o perfil para armazenamento em JSON."""
        return {
            "cooperation": self.cooperation,
            "discourse": self.discourse,
            "emotionality": self.emotionality,
            "info_control": self.info_control,
            "attitude": self.attitude,
        }
