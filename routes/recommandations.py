"""
Route de recommandations culinaires déterministes.
"""

from fastapi import APIRouter, Depends

try:
    from ..schemas.recommandations import ReponseRecommandation, RequeteRecommandation
    from ..securite import verifier_cle_ia
    from ..services.moteur_recommandations import calculer_recommandations
except (ImportError, ValueError):
    try:
        from schemas.recommandations import ReponseRecommandation, RequeteRecommandation
        from securite import verifier_cle_ia
        from services.moteur_recommandations import calculer_recommandations
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.recommandations import ReponseRecommandation, RequeteRecommandation
        from ayyouServiceIA.securite import verifier_cle_ia
        from ayyouServiceIA.services.moteur_recommandations import calculer_recommandations

routeur = APIRouter(prefix="/ia/recommandations", tags=["Recommandations"])


@routeur.post("/", response_model=ReponseRecommandation, dependencies=[Depends(verifier_cle_ia)])
def obtenir_recommandations(requete: RequeteRecommandation):
    return calculer_recommandations(requete)
