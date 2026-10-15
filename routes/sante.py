"""
Route de santé (health check) pour supervision.
"""

from fastapi import APIRouter
from ..config import parametres

routeur = APIRouter(prefix="/ia", tags=["Santé"])


@routeur.get("/sante/")
def verifier_sante():
    return {
        "statut": "OK",
        "service": parametres.NOM_SERVICE,
        "version": parametres.VERSION,
    }
