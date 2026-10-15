"""
Route de recommandations culinaires déterministes.
"""

from fastapi import APIRouter, Depends
from ..schemas.recommandations import ReponseRecommandation, RequeteRecommandation
from ..securite import verifier_cle_ia
from ..services.moteur_recommandations import calculer_recommandations

routeur = APIRouter(prefix="/ia/recommandations", tags=["Recommandations"])


@routeur.post("/", response_model=ReponseRecommandation, dependencies=[Depends(verifier_cle_ia)])
def obtenir_recommandations(requete: RequeteRecommandation):
    return calculer_recommandations(requete)
