"""
Route du chatbot culinaire sous contrainte budgétaire.
"""

from fastapi import APIRouter, Depends

try:
    from ..schemas.chatbot import MessageChatbot, ReponseChatbot
    from ..securite import verifier_cle_ia
    from ..services.moteur_chatbot import traiter_message_chatbot
except (ImportError, ValueError):
    try:
        from schemas.chatbot import MessageChatbot, ReponseChatbot
        from securite import verifier_cle_ia
        from services.moteur_chatbot import traiter_message_chatbot
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.chatbot import MessageChatbot, ReponseChatbot
        from ayyouServiceIA.securite import verifier_cle_ia
        from ayyouServiceIA.services.moteur_chatbot import traiter_message_chatbot

routeur = APIRouter(prefix="/ia/chatbot", tags=["Chatbot"])


@routeur.post("/", response_model=ReponseChatbot, dependencies=[Depends(verifier_cle_ia)])
def dialoguer_avec_chatbot(message: MessageChatbot):
    return traiter_message_chatbot(message)
