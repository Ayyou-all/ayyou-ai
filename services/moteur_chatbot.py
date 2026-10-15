"""
Moteur conversationnel culinaire AYYOU (Chatbot sous budget).
Analyse les requêtes gourmandes en langage naturel et propose des plats réels commandables.
"""

import re
from typing import List, Optional, Tuple

try:
    from ..schemas.chatbot import MessageChatbot, ReponseChatbot
    from ..schemas.recommandations import PlatCandidat
except (ImportError, ValueError):
    try:
        from schemas.chatbot import MessageChatbot, ReponseChatbot
        from schemas.recommandations import PlatCandidat
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.chatbot import MessageChatbot, ReponseChatbot
        from ayyouServiceIA.schemas.recommandations import PlatCandidat


def extraire_budget_depuis_texte(texte: str) -> Optional[int]:
    """Extrait un montant en FCFA formulé dans le message (ex: 2500 fcfa, 3000f, 4 000 cfa)."""
    motifs = [
        r"(\d+[\s\.]?\d*)\s*(?:fcfa|cfa|frs|f\b)",
        r"budget(?:\s+de)?\s*(\d+[\s\.]?\d*)",
        r"moins\s+de\s*(\d+[\s\.]?\d*)",
    ]
    for motif in motifs:
        match = re.search(motif, texte, re.IGNORECASE)
        if match:
            chiffres = re.sub(r"[\s\.]", "", match.group(1))
            try:
                val = int(chiffres)
                if 500 <= val <= 100000:
                    return val
            except ValueError:
                continue
    return None


def filtrer_et_classer_plats(
    plats: List[PlatCandidat],
    mots_cles: List[str],
    budget_max: Optional[int],
    quartier: Optional[str] = None,
) -> List[PlatCandidat]:
    """Sélectionne les plats correspondant aux mots-clés et sous le budget."""
    candidats = []
    for plat in plats:
        if budget_max is not None and plat.prix_fcfa > budget_max:
            continue

        texte = f"{plat.nom} {plat.description} {plat.categorie} {plat.nom_restaurant}".lower()
        score = 0
        if mots_cles:
            for mot in mots_cles:
                if mot.lower() in texte:
                    score += 10

        if score > 0 or not mots_cles:
            candidats.append((score, plat))

    candidats.sort(key=lambda x: (x[0], -x[1].prix_fcfa), reverse=True)
    return [plat for _, plat in candidats]


def traiter_message_chatbot(message: MessageChatbot) -> ReponseChatbot:
    texte = message.message.strip().lower()

    # 1. Détection du budget
    budget = message.budget_fcfa or extraire_budget_depuis_texte(texte)

    # 2. Détection d'intention et mots-clés gastronomiques sénégalais
    mots_cles_recherche = []
    specialites = [
        "thieb", "ceebu", "yassa", "mafe", "dibi", "pastels", "fataya", "nem",
        "burger", "pizza", "chawarma", "poulet", "poisson", "crevette", "brochette",
        "salade", "jus", "bouye", "bissap", "dessert"
    ]
    for sp in specialites:
        if sp in texte:
            mots_cles_recherche.append(sp)

    # Détection de l'intention
    if any(salut in texte for salut in ["bonjour", "salut", "salam", "coucou", "hello", "na nga def"]):
        if not mots_cles_recherche and not budget:
            return ReponseChatbot(
                texte_reponse="Salam ! Bienvenue sur AYYOU. Que souhaitez-vous déguster aujourd'hui ? Dites-moi votre envie (Thieb, Yassa, Dibi, Burger...) ou votre budget, et je vous trouve les meilleures adresses de Dakar !",
                plats_suggeres_ids=[],
                budget_respecte=True,
                intention_detectee="SALUTATION",
            )

    # 3. Filtrage des plats
    plats_trouves = filtrer_et_classer_plats(
        plats=message.plats_disponibles,
        mots_cles=mots_cles_recherche,
        budget_max=budget,
        quartier=message.quartier,
    )

    ids_suggeres = [p.id for p in plats_trouves[:4]]

    # 4. Rédaction de la réponse
    if not plats_trouves:
        if budget:
            rep = (
                f"Je n'ai pas trouvé de plat correspondant exactement sous votre budget de {budget:,} FCFA. "
                "Essayez d'augmenter légèrement votre budget ou de choisir une autre spécialité gourmande !"
            )
        else:
            rep = (
                "Je n'ai pas trouvé de plat correspondant à votre recherche pour le moment. "
                "N'hésitez pas à explorer notre fil d'accueil vidéo pour découvrir d'autres spécialités !"
            )
        return ReponseChatbot(
            texte_reponse=rep,
            plats_suggeres_ids=[],
            budget_respecte=False if budget else True,
            intention_detectee="RECHERCHE_SANS_RESULTAT",
        )

    # Formulation de la suggestion
    intro = "Voici mes meilleures recommandations pour vous régaler"
    if budget:
        intro += f" avec un budget de {budget:,} FCFA"
    intro += " :"

    details = []
    for plat in plats_trouves[:3]:
        details.append(f"• **{plat.nom}** chez *{plat.nom_restaurant}* ({plat.prix_fcfa:,} FCFA)")

    conclusion = "\n\n" + "\n".join(details) + "\n\n👉 Vous pouvez cliquer directement sur les cartes ci-dessous pour commander en 1 clic !"

    return ReponseChatbot(
        texte_reponse=intro + conclusion,
        plats_suggeres_ids=ids_suggeres,
        budget_respecte=True,
        intention_detectee="SUGGESTION_PLATS",
    )
