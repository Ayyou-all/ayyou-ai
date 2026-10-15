"""
Route de génération du rapport hebdomadaire du gérant.
"""

from fastapi import APIRouter, Depends

try:
    from ..schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
    from ..securite import verifier_cle_ia
    from ..services.moteur_rapport import generer_rapport_hebdomadaire
except (ImportError, ValueError):
    try:
        from schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
        from securite import verifier_cle_ia
        from services.moteur_rapport import generer_rapport_hebdomadaire
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
        from ayyouServiceIA.securite import verifier_cle_ia
        from ayyouServiceIA.services.moteur_rapport import generer_rapport_hebdomadaire

routeur = APIRouter(prefix="/ia/rapport", tags=["Rapport"])


@routeur.post("/", response_model=ReponseRapportHebdo, dependencies=[Depends(verifier_cle_ia)])
def obtenir_rapport_hebdo(requete: RequeteRapportHebdo):
    return generer_rapport_hebdomadaire(requete)
