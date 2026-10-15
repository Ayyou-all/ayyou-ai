"""
Module de sécurité interne pour le microservice IA AYYOU.
Vérifie que chaque requête provient du backend Django autorisé via un en-tête partagé.
"""

from fastapi import Header, HTTPException, status
from .config import parametres


def verifier_cle_ia(x_ayyou_ia_key: str = Header(..., alias="X-AYYOU-IA-KEY")):
    """
    Dépendance FastAPI garantissant qu'aucun client externe non autorisé n'appelle l'IA en direct.
    """
    if x_ayyou_ia_key != parametres.CLE_SECRETE_INTERNE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clé d'autorisation interne du service IA invalide ou manquante.",
        )
    return True
