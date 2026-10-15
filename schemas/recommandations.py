"""
Schémas Pydantic pour le moteur de recommandation culinaire.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PlatCandidat(BaseModel):
    id: int
    nom: str
    description: str = ""
    prix_fcfa: int
    restaurant_id: int
    nom_restaurant: str
    categorie: str = ""
    nombre_likes: int = 0
    nombre_commandes: int = 0


class RequeteRecommandation(BaseModel):
    utilisateur_id: Optional[int] = None
    plats: List[PlatCandidat]
    historique_commandes_ids: List[int] = Field(default_factory=list)
    plats_aimes_ids: List[int] = Field(default_factory=list)
    budget_max_fcfa: Optional[int] = None
    heure_actuelle: Optional[int] = Field(None, ge=0, le=23, description="Heure locale de Dakar (0 à 23)")
    limite: int = Field(default=10, ge=1, le=50)


class PlatRecommande(BaseModel):
    id: int
    nom: str
    nom_restaurant: str
    prix_fcfa: int
    score_pertinence: float
    raison_recommandation: str


class ReponseRecommandation(BaseModel):
    recommandations: List[PlatRecommande]
    contexte_moment: str
    total: int
