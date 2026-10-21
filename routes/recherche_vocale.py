"""
Route de la recherche vocale intelligente : phrase dictée -> filtres de recherche.
"""

from fastapi import APIRouter, Depends

try:
    from ..schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
    from ..securite import verifier_cle_ia
    from ..services.moteur_recherche_vocale import analyser_recherche_vocale
except (ImportError, ValueError):
    try:
        from schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
        from securite import verifier_cle_ia
        from services.moteur_recherche_vocale import analyser_recherche_vocale
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.recherche_vocale import ReponseRechercheVocale, RequeteRechercheVocale
        from ayyouServiceIA.securite import verifier_cle_ia
        from ayyouServiceIA.services.moteur_recherche_vocale import analyser_recherche_vocale

routeur = APIRouter(prefix="/ia/recherche-vocale", tags=["Recherche vocale"])


@routeur.post("/", response_model=ReponseRechercheVocale, dependencies=[Depends(verifier_cle_ia)])
def analyser_phrase(requete: RequeteRechercheVocale):
    return analyser_recherche_vocale(requete)
