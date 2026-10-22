"""
Route de prévisions de flux et coups de feu pour les restaurants.
"""

#from fastapi import APIRouter, Depends

try:
    from ..schemas.previsions import ReponsePrevisions, RequetePrevisions
    from ..securite import verifier_cle_ia
    from ..services.moteur_previsions import calculer_previsions_flux
except (ImportError, ValueError):
    try:
        from schemas.previsions import ReponsePrevisions, RequetePrevisions
        from securite import verifier_cle_ia
        from services.moteur_previsions import calculer_previsions_flux
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.previsions import ReponsePrevisions, RequetePrevisions
        from ayyouServiceIA.securite import verifier_cle_ia
        from ayyouServiceIA.services.moteur_previsions import calculer_previsions_flux

#routeur = APIRouter(prefix="/ia/previsions", tags=["Prévisions"])


#@routeur.post("/", response_model=ReponsePrevisions, dependencies=[Depends(verifier_cle_ia)])
def generer_previsions_flux(requete: RequetePrevisions):
    return calculer_previsions_flux(requete)
