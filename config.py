"""
Configuration du microservice d'Intelligence Artificielle AYYOU.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class ParametresIA:
    NOM_SERVICE: str = "AYYOU Intelligence Artificielle (Microservice)"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("AYYOU_IA_DEBUG", "True").lower() in ("true", "1", "yes")
    CLE_SECRETE_INTERNE: str = os.getenv("AYYOU_SERVICE_IA_CLE_INTERNE", "cle-secrete-interne-ayyou-ia-2026")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    LLM_MODELE: str = os.getenv("AYYOU_LLM_MODELE", "minimax/minimax-m3.1-flash:free")
    LLM_TIMEOUT: float = float(os.getenv("AYYOU_LLM_TIMEOUT", "3.5"))
    HOTE: str = os.getenv("AYYOU_IA_HOTE", "127.0.0.1")
    PORT: int = int(os.getenv("AYYOU_IA_PORT", "8001"))


parametres = ParametresIA()
