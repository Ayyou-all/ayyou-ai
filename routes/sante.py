"""
Route de santé (health check) pour supervision.
"""

from fastapi import APIRouter

try:
    from ..config import parametres
except (ImportError, ValueError):
    try:
        from config import parametres
    except (ImportError, ValueError):
        from ayyouServiceIA.config import parametres

routeur = APIRouter(prefix="/ia", tags=["Santé"])


@routeur.get("/sante/")
def verifier_sante():
    return {
        "statut": "OK",
        "service": parametres.NOM_SERVICE,
        "version": parametres.VERSION,
    }
