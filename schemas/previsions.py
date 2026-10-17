"""
Schémas Pydantic pour les prévisions de flux et tendances restaurant.
"""

from typing import List
from pydantic import BaseModel, Field


class VenteHistorique(BaseModel):
    jour_semaine: int = Field(..., ge=0, le=6)
    heure: int = Field(..., ge=0, le=23)
    quantite_commandes: int = Field(default=0, ge=0)
    chiffre_affaires_fcfa: int = Field(default=0, ge=0)


class RequetePrevisions(BaseModel):
    restaurant_id: int
    nom_restaurant: str
    historique_ventes: List[VenteHistorique] = Field(default_factory=list)
    jour_cible: int = Field(default=4, ge=0, le=6, description="0=Lundi ... 4=Vendredi ... 6=Dimanche")
    nombre_semaines: int = Field(default=4, ge=1, description="Nombre de semaines couvertes par l'historique")


class PrevisionHeure(BaseModel):
    heure: int
    commandes_estimees: float
    intensite: str  # "CALME" | "MODÉRÉ" | "COUP_DE_FEU"


class ReponsePrevisions(BaseModel):
    restaurant_id: int
    nom_restaurant: str
    previsions_par_heure: List[PrevisionHeure]
    heure_de_pointe: str
    conseils_organisation: List[str]
