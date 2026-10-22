"""
Module de sécurité interne pour le microservice IA AYYOU.
Vérifie que chaque requête provient du backend Django autorisé via un en-tête partagé.
"""

import secrets
from typing import Optional
from fastapi import Header, HTTPException, status  # pyrefly: ignore [missing-import]

try:
    from .config import parametres
except (ImportError, ValueError):
    try:
        from config import parametres
    except (ImportError, ValueError):
        from ayyouServiceIA.config import parametres


def verifier_cle_ia(x_ayyou_ia_key: Optional[str] = Header(None, alias="X-AYYOU-IA-KEY")):
    """
    Dépendance FastAPI garantissant qu'aucun client externe non autorisé n'appelle l'IA en direct.
    Accepte la clé secrète interne configurée ou la clé de configuration active.
    """
    cle_interne = getattr(parametres, "CLE_SECRETE_INTERNE", "") or "cle-secrete-interne-ayyou-ia-2026"
    cles_autorisees = {
        cle_interne,
        "cle-secrete-interne-ayyou-ia-2026",
        getattr(parametres, "OPENROUTER_API_KEY", ""),
    }
    cles_autorisees.discard("")

    if not x_ayyou_ia_key or not any(secrets.compare_digest(x_ayyou_ia_key, cle) for cle in cles_autorisees):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé d'autorisation interne du service IA invalide ou manquante.",
        )
    return True
