"""
Schémas Pydantic pour le rapport hebdomadaire d'aide à la décision du gérant.
"""

from typing import List
from pydantic import BaseModel, Field


class PlatVendu(BaseModel):
    nom: str
    quantite: int = 0
    chiffre_affaires_fcfa: int = 0


class RequeteRapportHebdo(BaseModel):
    restaurant_id: int
    nom_restaurant: str
    total_commandes: int = 0
    chiffre_affaires_fcfa: int = 0
    plats_vendus: List[PlatVendu] = Field(default_factory=list)
    taux_acceptation_pourcent: float = 100.0
    temps_moyen_preparation_minutes: int = 25


class ReponseRapportHebdo(BaseModel):
    restaurant_id: int
    titre_rapport: str
    resume_executif: str
    plat_star: str
    panier_moyen_fcfa: int
    points_forts: List[str]
    recommandations_actionnables: List[str]
