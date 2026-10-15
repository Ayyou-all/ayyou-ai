"""
Route de prévisions de flux et coups de feu pour les restaurants.
"""

from fastapi import APIRouter, Depends
from ..schemas.previsions import ReponsePrevisions, RequetePrevisions
from ..securite import verifier_cle_ia
from ..services.moteur_previsions import calculer_previsions_flux

routeur = APIRouter(prefix="/ia/previsions", tags=["Prévisions"])


@routeur.post("/", response_model=ReponsePrevisions, dependencies=[Depends(verifier_cle_ia)])
def generer_previsions_flux(requete: RequetePrevisions):
    return calculer_previsions_flux(requete)
