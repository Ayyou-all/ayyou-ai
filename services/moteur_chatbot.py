"""
Moteur conversationnel culinaire AYYOU (Chef AYYOU - Assistant Culinaire IA).

Architecture :
1. Détection des garde-fous de sécurité et confidentialité (Super Admin, secrets, injection).
2. Extraction robuste du budget (chiffres, expressions verbales 'j'ai 500', toutes lettres, k/mille).
3. Gestion conversationnelle naturelle (Salutations, identité, contexte multi-tours sans base de données).
4. Filtrage et validation déterministe STRICTE du budget : prix_plat <= budget_max.
5. Formulation naturelle par LLM (OpenRouter) avec garde-fous stricts et repli déterministe bienveillant.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx

try:
    from ..config import parametres
    from ..schemas.chatbot import MessageChatbot, MessageHistorique, ReponseChatbot
    from ..schemas.recommandations import PlatCandidat
except (ImportError, ValueError):
    try:
        from config import parametres
        from schemas.chatbot import MessageChatbot, MessageHistorique, ReponseChatbot
        from schemas.recommandations import PlatCandidat
    except (ImportError, ValueError):
        from ayyouServiceIA.config import parametres
        from ayyouServiceIA.schemas.chatbot import MessageChatbot, MessageHistorique, ReponseChatbot
        from ayyouServiceIA.schemas.recommandations import PlatCandidat

logger = logging.getLogger("ayyou.ia.chatbot")

# Dictionnaire de conversion des nombres écrits en toutes lettres en FCFA
NOMBRES_TEXTE = {
    "cinq cents": 500,
    "cinq cent": 500,
    "cinq-cents": 500,
    "cinq-cent": 500,
    "six cents": 600,
    "sept cents": 700,
    "huit cents": 800,
    "neuf cents": 900,
    "mille": 1000,
    "mille cinq cents": 1500,
    "mille cinq cent": 1500,
    "deux mille": 2000,
    "deux mille cinq cents": 2500,
    "deux mille cinq cent": 2500,
    "trois mille": 3000,
    "trois mille cinq cents": 3500,
    "quatre mille": 4000,
    "cinq mille": 5000,
    "six mille": 6000,
    "sept mille": 7000,
    "huit mille": 8000,
    "neuf mille": 9000,
    "dix mille": 10000,
    "quinze mille": 15000,
    "vingt mille": 20000,
}

REPONSE_SECURITE_CONFIDENTIELLE = (
    "Désolé, je n'ai pas accès à ces informations confidentielles et je ne peux pas les communiquer. "
    "Je peux toutefois vous aider avec les informations publiques et les fonctionnalités accessibles d'AYYOU."
)


def detecter_demande_securite_ou_injection(texte: str) -> bool:
    """
    Vérifie si la requête tente d'accéder à des données confidentielles ou d'injecter des instructions.
    Ne laisse rien passer vers le LLM.
    """
    if not texte:
        return False
    texte_lower = texte.lower()

    motifs_interdits = [
        # Super admin / mots de passe / comptes
        r"(?:super\s*admin|administrateur|mots?\s*de\s*passe|passwords?|identifiants?\s*admin|comptes?\s*admin)",
        # Clés, tokens, variables d'environnement
        r"(?:cl[ée]s?\s*api|api\s*keys?|jwt|secrets?|variables?\s*d['’]environnement|\.env|bearer|cl[ée]s?\s*secr[èe]tes?)",
        # Base de données, tables, dump
        r"(?:base\s*de\s*donn[ée]es|database|select\s+.*from|drop\s+table|dump|sql|django_migrations)",
        # Commandes / paiements d'autres utilisateurs
        r"(?:autres?\s*clients?|autres?\s*commandes?|autres?\s*utilisateurs?|dossiers?\s*clients?|autres?\s*paiements?)",
        # Injections de prompt / jailbreaks
        r"(?:ignore\s+(?:tes|vos|toutes\s+les)\s+r[èe]gles|r[ée]v[èe]le\s+(?:ton|votre)\s+prompt|prompt\s*syst[èe]me)",
        r"(?:fais\s+comme\s+si\s+tu\s+[ée]tais\s+admin|fais\s+comme\s+si\s+j['’][ée]tais\s+admin|mode\s+d[ée]veloppeur)",
        r"(?:bypass|contourne|jailbreak|dis[- ]moi\s+tes\s+instructions\s+initiales)",
    ]

    for motif in motifs_interdits:
        if re.search(motif, texte_lower):
            return True
    return False


def extraire_budget_robuste(texte: str) -> Optional[int]:
    """
    Extrait avec précision tout budget exprimé en FCFA.
    Gère les formulations verbales ('j'ai 500', 'je dispose de 1500'),
    les devises ('500 francs', '500 F', '500 FCFA'), les contraintes ('moins de 2000'),
    les montants en toutes lettres ('cinq cents francs') et '2,5 mille'.
    """
    if not texte:
        return None
    texte_clean = texte.lower().strip()

    # 1. Format '2,5 mille' ou '2.5 mille'
    match_k = re.search(r"(\d+(?:[,\.]\d+)?)\s*mille", texte_clean)
    if match_k:
        val_str = match_k.group(1).replace(",", ".")
        try:
            val_float = float(val_str)
            return int(val_float * 1000)
        except ValueError:
            pass

    # 2. Nombres en toutes lettres
    for nom_texte, valeur in sorted(NOMBRES_TEXTE.items(), key=lambda x: -len(x[0])):
        if nom_texte in texte_clean:
            return valeur

    # 3. Motifs regex ordonnés
    motifs = [
        # Explicit currency suffix: '500 fcfa', '1 500 francs', '3000 cfa', '500f', '4500 frs'
        r"(\d+[\s\.]?\d*)\s*(?:fcfa|cfa|frs|francs?|f\b)",
        # Keywords 'budget', 'budjet', 'tarif', 'somme'
        r"(?:budget|budjet|tarif|somme)(?:\s*(?:de|max|maximum|environ|égal|egal|:|=))?\s*(\d+[\s\.]?\d*)",
        # Ceiling constraints: 'moins de 3000', 'maximum 2500', 'max 2500', 'pas dépasser 3000', 'sous 2000'
        r"(?:moins\s+de|maximum|max|ne\s+pas\s+dépasser|pas\s+dépasser|sous|inférieur\s+à)\s*(\d+[\s\.]?\d*)",
        # Verb phrase: 'j'ai 500', 'jai 500', 'je dispose de 1500', 'je peux mettre 2500'
        r"(?:j['’]?\s*ai|jai|dispose\s+de|peux\s+mettre|mettre\s+au\s+max)\s*(\d+[\s\.]?\d*)",
        # Prepositional expressions: 'pour 2000', 'avec 1500', 'de 2500', 'à moins de 3000'
        r"(?:pour|avec|de|à|a)\s*(\d+[\s\.]?\d*)\s*(?:fcfa|cfa|frs|francs?|f\b)?",
        # Isolated 3-5 digit number (ex: 'jai 500 que me propose tu', 'thieb 2500')
        r"\b(\d{3,5})\b",
    ]

    for motif in motifs:
        match = re.search(motif, texte_clean)
        if match:
            chiffres = re.sub(r"[\s\.]", "", match.group(1))
            try:
                val = int(chiffres)
                if 200 <= val <= 100000:
                    return val
            except ValueError:
                continue

    return None


# Rétrocompatibilité pour les modules consommateurs (ex: recherche vocale)
extraire_budget_depuis_texte = extraire_budget_robuste


def filtrer_et_classer_plats(
    plats: List[PlatCandidat],
    termes_recherche: List[str],
    budget_max: Optional[int],
    quartier: Optional[str] = None,
) -> List[PlatCandidat]:
    """
    Filtre et classe les plats candidats.
    RÈGLE ABSOLUE : tout plat dont le prix dépasse budget_max est STRICTEMENT éliminé.
    """
    candidats = []
    quartier_clean = quartier.lower().strip() if quartier else None

    for plat in plats:
        # Contrôle strict du budget
        if budget_max is not None and plat.prix_fcfa > budget_max:
            continue

        texte_plat = f"{plat.nom} {plat.description} {plat.categorie} {plat.nom_restaurant}".lower()
        score = 0

        # Correspondance mots-clés
        if termes_recherche:
            for terme in termes_recherche:
                if terme.lower() in texte_plat:
                    score += 15

        # Correspondance quartier
        if quartier_clean and quartier_clean in texte_plat:
            score += 20

        # Bonus popularité légère
        score += min(plat.nombre_likes, 10)

        # Si recherche explicite, n'inclure que les plats qui ont un score positif
        if score > 0 or not termes_recherche:
            candidats.append((score, plat))

    # Tri : d'abord le score de pertinence, puis le prix croissant (accessibilité)
    candidats.sort(key=lambda x: (x[0], -x[1].prix_fcfa), reverse=True)
    return [plat for _, plat in candidats]


def appeler_llm_conversationnel(
    message_utilisateur: str,
    budget: Optional[int],
    plats_selectionnes: List[PlatCandidat],
    historique: Optional[List[MessageHistorique]] = None,
    intention: str = "SUGGESTION",
) -> Optional[str]:
    """
    Génère une réponse naturelle avec le LLM configuré (OpenRouter).
    Fournit l'historique conversationnel de la session pour la continuité de dialogue.
    """
    cle_api = getattr(parametres, "OPENROUTER_API_KEY", "") or os.getenv("OPENROUTER_API_KEY", "")
    if not cle_api or not cle_api.startswith("sk-or-"):
        # Vérification si ancienne clé AYYOU_CLE_SECRETE_IA est valide
        cle_secours = os.getenv("AYYOU_CLE_SECRETE_IA", "")
        if cle_secours.startswith("sk-or-"):
            cle_api = cle_secours
        else:
            return None

    lignes_plats = []
    for p in plats_selectionnes[:4]:
        lignes_plats.append(
            f"- {p.nom} de {p.nom_restaurant} | Prix: {p.prix_fcfa:,} FCFA | Description: {p.description or 'Spécialité maison'}"
        )
    contexte_plats = "\n".join(lignes_plats) if lignes_plats else "Aucun plat disponible sous ce critère."

    prompt_systeme = (
        "Tu es Chef AYYOU, l'assistant culinaire virtuel de la plateforme AYYOU à Dakar, Sénégal.\n"
        "Ton ton est chaleureux, poli, authentique et accueillant (expressions dakarorises bienveillantes comme 'Dalal ak jàmm !', 'Régalez-vous !').\n\n"
        "RÈGLES STRICTES DE SÉCURITÉ ET D'INTÉGRITÉ :\n"
        "1. Tu n'as AUCUN accès aux données administratives, mots de passe, clés secrètes ou commandes d'autres clients. Si on te les demande, refuse poliment.\n"
        "2. N'invente JAMAIS un plat, un prix ou un restaurant. Tu ne peux recommander QUE les plats explicitement fournis dans le catalogue ci-dessous.\n"
        "3. Respecte STRICTEMENT le budget du client s'il est mentionné. Si aucun plat n'est sous le budget, explique-le gentiment et demande s'il souhaite augmenter son budget ou voir les plats les moins chers.\n"
        "4. Réponds de façon concise (2 à 3 phrases claires et dynamiques). Invite le client à cliquer sur les cartes ci-dessous pour voir le détail ou ajouter au panier en 1 clic."
    )

    messages_llm = [{"role": "system", "content": prompt_systeme}]

    # Inclusion du contexte temporaire récent (maximum 4 derniers tours)
    if historique:
        for tour in historique[-4:]:
            role_llm = "user" if tour.role.lower() in ("user", "utilisateur") else "assistant"
            messages_llm.append({"role": role_llm, "content": tour.contenu})

    consigne_budget = f"Budget maximum strict : {budget:,} FCFA." if budget else "Aucun budget strict spécifié."

    consigne_tour = (
        f"Message actuel du client : \"{message_utilisateur}\"\n"
        f"Contrainte : {consigne_budget}\n"
        f"Plats réels validés en cuisine sous le budget :\n{contexte_plats}\n\n"
        "Formule ta réponse naturelle et personnalisée au client."
    )
    messages_llm.append({"role": "user", "content": consigne_tour})

    modele = getattr(parametres, "LLM_MODELE", "minimax/minimax-m3.1-flash:free")
    timeout = getattr(parametres, "LLM_TIMEOUT", 6.0)

    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {cle_api}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ayyou.sn",
            "X-Title": "Chef AYYOU FoodTech Dakar",
        }
        payload = {
            "model": modele,
            "messages": messages_llm,
            "max_tokens": 250,
            "temperature": 0.6,
        }

        with httpx.Client(timeout=timeout) as client:
            res = client.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                msg_obj = data["choices"][0].get("message", {})
                texte_rep = (msg_obj.get("content") or msg_obj.get("reasoning") or "").strip()
                if texte_rep:
                    return texte_rep
            else:
                logger.warning("OpenRouter a renvoyé le statut %s: %s", res.status_code, res.text)
    except Exception as exc:
        logger.warning("Le LLM distant n'a pas répondu (%s), bascule sur le modèle déterministe.", exc)

    return None


def traiter_message_chatbot(message: MessageChatbot) -> ReponseChatbot:
    """
    Point d'entrée du chatbot culinaire AYYOU.
    Exécute le parcours sécurisé, déterministe et conversationnel.
    """
    texte_brut = message.message.strip()
    texte_lower = texte_brut.lower()

    # 1. Garde-fou absolu de sécurité (Super admin, tokens, injection)
    if detecter_demande_securite_ou_injection(texte_brut):
        logger.warning("Tentative d'accès sécurisé ou prompt injection bloquée: %s", texte_brut[:60])
        return ReponseChatbot(
            texte_reponse=REPONSE_SECURITE_CONFIDENTIELLE,
            plats_suggeres_ids=[],
            budget_respecte=True,
            budget_detecte_fcfa=None,
            intention_detectee="SECURITE_REFUS",
        )

    # 2. Salutations et civilités
    mots_salutation = ["bonjour", "salut", "salam", "na nga def", "nanga def", "coucou", "hello", "bonsoir", "ça va", "ca va"]
    est_salutation_pure = any(re.search(rf"\b{re.escape(s)}\b", texte_lower) for s in mots_salutation)

    # 3. Questions d'identité et de rôle
    mots_identite = ["qui es-tu", "qui es tu", "t'appelles", "te nommes", "à quoi sers-tu", "a quoi sers tu", "ton role", "ton rôle", "c'est quoi ayyou"]
    est_question_identite = any(m in texte_lower for m in mots_identite)

    if est_question_identite:
        return ReponseChatbot(
            texte_reponse=(
                "Dalal ak jàmm ! Je suis Chef AYYOU, votre assistant culinaire virtuel. "
                "Je vous aide à trouver de délicieux plats traditionnels et spécialités à Dakar "
                "selon vos envies (Thieb, Yassa, Dibi, Burgers...) et votre budget précis en FCFA. "
                "Dites-moi simplement ce dont vous avez envie ou quel budget vous avez !"
            ),
            plats_suggeres_ids=[],
            budget_respecte=True,
            budget_detecte_fcfa=None,
            intention_detectee="PRESENTATION_IDENTITE",
        )

    # 4. Extraction robuste du budget
    budget = message.budget_fcfa or extraire_budget_robuste(texte_brut)

    # Si salutation pure sans envie culinaire ni budget
    if est_salutation_pure and not budget:
        specialites_test = ["thieb", "ceebu", "yassa", "mafe", "dibi", "pastels", "burger", "pizza", "chawarma", "poulet", "poisson"]
        if not any(sp in texte_lower for sp in specialites_test):
            return ReponseChatbot(
                texte_reponse=(
                    "Salam alikoum ! Bienvenue chez Chef AYYOU. Que souhaitez-vous déguster aujourd'hui à Dakar ? "
                    "Partagez-moi votre envie (Thieboudienne, Yassa, Dibi, Burger...) ou votre budget (ex : 3 000 FCFA), "
                    "et je vous déniche les meilleures adresses !"
                ),
                plats_suggeres_ids=[],
                budget_respecte=True,
                budget_detecte_fcfa=None,
                intention_detectee="SALUTATION",
            )

    # 5. Extraction des spécialités culinaires et mots-clés
    specialites_senegalaises = [
        "thieb", "ceebu", "thiéboudienne", "thieboudienne", "yassa", "mafe", "mafé",
        "dibi", "pastels", "fataya", "nem", "burger", "pizza", "chawarma", "poulet",
        "poisson", "crevette", "brochette", "salade", "jus", "bouye", "bissap", "dessert",
        "tacos", "viande", "ndambé", "ndambe"
    ]
    mots_cles = []
    for sp in specialites_senegalaises:
        if sp in texte_lower:
            mots_cles.append(sp)

    # Détection de demande relative "moins cher" en utilisant l'historique
    demande_moins_cher = "moins cher" in texte_lower or "plus abordable" in texte_lower or "plus economique" in texte_lower
    if demande_moins_cher and not budget and message.historique:
        # Recherche du budget précédent dans l'historique
        for h in reversed(message.historique):
            b_prec = extraire_budget_robuste(h.contenu)
            if b_prec:
                budget = int(b_prec * 0.8)  # cherche 20% moins cher
                break

    # Si demande "moins cher" sans budget préalable
    if demande_moins_cher and not budget:
        # Trouver le plat le moins cher du catalogue
        if message.plats_disponibles:
            plat_min = min(message.plats_disponibles, key=lambda p: p.prix_fcfa)
            budget = plat_min.prix_fcfa

    # 6. Filtrage STRICT des plats (prix_plat <= budget)
    plats_conformes = filtrer_et_classer_plats(
        plats=message.plats_disponibles,
        termes_recherche=mots_cles,
        budget_max=budget,
        quartier=message.quartier,
    )

    # 7. Gestion de l'absence de résultats sous le budget (Cas critique : 500 FCFA)
    if not plats_conformes:
        if budget:
            rep = (
                f"Avec un budget de {budget:,} FCFA, je n'ai pas trouvé de plat disponible dans cette gamme de prix "
                "pour le moment. Souhaites-tu que je recherche les options les moins chères ou préfères-tu augmenter ton budget ?"
            )
        else:
            rep = (
                "Je n'ai pas trouvé de plat correspondant exactement à votre recherche pour le moment. "
                "N'hésitez pas à modifier vos critères ou à explorer le catalogue d'accueil pour voir toutes nos spécialités !"
            )
        return ReponseChatbot(
            texte_reponse=rep,
            plats_suggeres_ids=[],
            budget_respecte=False if budget else True,
            budget_detecte_fcfa=budget,
            intention_detectee="AUCUN_PLAT_SOUS_BUDGET",
        )

    # Sélection des meilleurs plats conformes (maximum 4)
    plats_selectionnes = plats_conformes[:4]
    ids_selectionnes = [p.id for p in plats_selectionnes]

    # 8. Appel au LLM pour formuler une réponse naturelle et dynamique
    reponse_llm = appeler_llm_conversationnel(
        message_utilisateur=texte_brut,
        budget=budget,
        plats_selectionnes=plats_selectionnes,
        historique=message.historique,
        intention="SUGGESTION_PLATS",
    )

    if reponse_llm:
        return ReponseChatbot(
            texte_reponse=reponse_llm,
            plats_suggeres_ids=ids_selectionnes,
            budget_respecte=True,
            budget_detecte_fcfa=budget,
            intention_detectee="SUGGESTION_PLATS",
        )

    # 9. Gabarit de repli déterministe de haute qualité (si LLM indisponible ou timeout)
    if budget:
        intro = f"Voici d'excellents plats sous votre budget de {budget:,} FCFA sélectionnés à Dakar :"
    else:
        intro = "Voici notre sélection des spécialités dakarorises recommandées :"

    lignes = []
    for plat in plats_selectionnes[:3]:
        desc = f" ({plat.description})" if plat.description else ""
        lignes.append(f"• **{plat.nom}** chez *{plat.nom_restaurant}* — **{plat.prix_fcfa:,} FCFA**{desc}")

    conclusion = "\n\n" + "\n".join(lignes) + "\n\n👉 *Cliquez directement sur une carte ci-dessous pour voir le détail ou ajouter au panier !*"

    return ReponseChatbot(
        texte_reponse=intro + conclusion,
        plats_suggeres_ids=ids_selectionnes,
        budget_respecte=True,
        budget_detecte_fcfa=budget,
        intention_detectee="SUGGESTION_PLATS",
    )
