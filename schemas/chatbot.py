"""
Schémas Pydantic pour le Chatbot culinaire AYYOU.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from .recommandations import PlatCandidat


class MessageChatbot(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    budget_fcfa: Optional[int] = Field(None, ge=100)
    quartier: Optional[str] = None
    plats_disponibles: List[PlatCandidat] = Field(default_factory=list)


class ReponseChatbot(BaseModel):
    texte_reponse: str
    plats_suggeres_ids: List[int]
    budget_respecte: bool
    intention_detectee: str
