"""
Route de génération du rapport hebdomadaire du gérant.
"""

from fastapi import APIRouter, Depends
from ..schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
from ..securite import verifier_cle_ia
from ..services.moteur_rapport import generer_rapport_hebdomadaire

routeur = APIRouter(prefix="/ia/rapport", tags=["Rapport"])


@routeur.post("/", response_model=ReponseRapportHebdo, dependencies=[Depends(verifier_cle_ia)])
def obtenir_rapport_hebdo(requete: RequeteRapportHebdo):
    return generer_rapport_hebdomadaire(requete)
