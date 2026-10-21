"""
Schémas Pydantic de la recherche vocale intelligente AYYOU.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RequeteRechercheVocale(BaseModel):
    texte: str = Field(..., min_length=1, max_length=300)
    # Quartiers où se trouvent de vrais restaurants (fournis par le backend)
    quartiers_connus: List[str] = Field(default_factory=list)


class ReponseRechercheVocale(BaseModel):
    texte_normalise: str
    # Spécialités reconnues (ex. "thieb") et toutes leurs orthographes, pour la recherche
    specialites: List[str]
    termes_recherche: List[str]
    # Mots restants qui peuvent être un nom de restaurant (ex. "loutcha")
    mots_libres: List[str]
    budget_max_fcfa: Optional[int]
    quartier: Optional[str]
    tri: Optional[str]  # "PRIX" (pas cher) ou None
    ouvert_seulement: bool
