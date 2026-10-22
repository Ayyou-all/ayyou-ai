"""
Schémas Pydantic pour le Chatbot culinaire AYYOU.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator
from .recommandations import PlatCandidat


class MessageHistorique(BaseModel):
    role: str = Field(..., description="Role de l'emetteur: 'user' ou 'assistant'")
    contenu: str = Field("", max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def adapter_champs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "contenu" not in data and "content" in data:
                data["contenu"] = data["content"]
            elif "contenu" not in data and "texte" in data:
                data["contenu"] = data["texte"]
        return data


class MessageChatbot(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    budget_fcfa: Optional[int] = Field(None, ge=100)
    quartier: Optional[str] = None
    historique: List[MessageHistorique] = Field(default_factory=list)
    plats_disponibles: List[PlatCandidat] = Field(default_factory=list)


class ReponseChatbot(BaseModel):
    texte_reponse: str
    plats_suggeres_ids: List[int]
    budget_respecte: bool
    budget_detecte_fcfa: Optional[int] = None
    intention_detectee: str
