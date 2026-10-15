"""
Configuration du microservice d'Intelligence Artificielle AYYOU.
"""

import os


class ParametresIA:
    NOM_SERVICE: str = "AYYOU Intelligence Artificielle (Microservice)"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("AYYOU_IA_DEBUG", "True").lower() in ("true", "1", "yes")
    CLE_SECRETE_INTERNE: str = os.getenv("AYYOU_CLE_SECRETE_IA", "cle-secrete-interne-ayyou-ia-2026")
    HOTE: str = os.getenv("AYYOU_IA_HOTE", "127.0.0.1")
    PORT: int = int(os.getenv("AYYOU_IA_PORT", "8001"))


parametres = ParametresIA()
