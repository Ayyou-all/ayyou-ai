"""
Schémas Pydantic pour le rapport hebdomadaire d'aide à la décision du gérant.
"""

from typing import List, Optional
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
    # None = donnée encore inconnue (jamais de valeur par défaut inventée)
    taux_acceptation_pourcent: Optional[float] = None
    temps_moyen_preparation_minutes: Optional[int] = None


class ReponseRapportHebdo(BaseModel):
    restaurant_id: int
    titre_rapport: str
    resume_executif: str
    plat_star: str
    panier_moyen_fcfa: int
    points_forts: List[str]
    recommandations_actionnables: List[str]
