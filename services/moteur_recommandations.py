"""
Moteur déterministe de recommandation culinaire AYYOU.

Prend en compte :
1. Le moment de la journée à Dakar (déjeuner traditionnel sénégalais vs dîner grillades/dibiterie)
2. Le plafond budgétaire éventuel (filtre strict)
3. L'affinité de l'utilisateur (historique des commandes passées et des mentions J'aime)
4. La popularité intrinsèque du plat (commandes globales et likes)
"""

from typing import List, Tuple
from ..schemas.recommandations import (
    PlatCandidat,
    PlatRecommande,
    ReponseRecommandation,
    RequeteRecommandation,
)


def determiner_contexte_moment(heure: int) -> Tuple[str, List[str], List[str]]:
    """
    Retourne (nom_moment, mots_cles_favorises, mots_cles_penalises).
    Heure de Dakar (GMT).
    """
    if 11 <= heure <= 15:
        return (
            "Déjeuner traditionnel de midi",
            ["thieb", "ceebu", "yassa", "mafe", "poisson", "riz", "c'est bon", "soupe kandia"],
            ["chawarma", "crepe"],
        )
    elif 18 <= heure <= 23:
        return (
            "Dîner & Soirée gourmande",
            ["dibi", "grillade", "poulet", "burger", "brochette", "chawarma", "pizza", "viande"],
            [],
        )
    elif 6 <= heure <= 10:
        return (
            "Petit-déjeuner & Matinée",
            ["cafe", "croissant", "omelette", "pain", "beignet", "jus", "bouye", "bissap"],
            ["dibi", "thieb"],
        )
    else:
        return (
            "Collation & Goûter de l'après-midi",
            ["pastels", "fataya", "nem", "jus", "dessert", "glace", "bouye", "bissap"],
            [],
        )


def calculer_recommandations(requete: RequeteRecommandation) -> ReponseRecommandation:
    heure = requete.heure_actuelle if requete.heure_actuelle is not None else 13
    moment_nom, mots_favorises, mots_penalises = determiner_contexte_moment(heure)

    scores_plats: List[Tuple[float, PlatCandidat, str]] = []

    for plat in requete.plats:
        # 1. Filtre strict de budget
        if requete.budget_max_fcfa is not None and plat.prix_fcfa > requete.budget_max_fcfa:
            continue

        score = 50.0  # Base
        raisons = []

        # 2. Bonus / Malus temporel (mots-clés dans le nom ou la description)
        texte_plat = f"{plat.nom} {plat.description} {plat.categorie}".lower()
        if any(mot in texte_plat for mot in mots_favorises):
            score += 25.0
            raisons.append(f"Parfait pour votre {moment_nom.lower()}")
        elif any(mot in texte_plat for mot in mots_penalises):
            score -= 15.0

        # 3. Affinité historique de commandes
        if plat.id in requete.historique_commandes_ids:
            score += 20.0
            raisons.append("Vous avez déjà aimé ce plat")

        # 4. Affinité mention J'aime
        if plat.id in requete.plats_aimes_ids:
            score += 15.0
            raisons.append("Présent dans vos coups de cœur")

        # 5. Popularité générale (logarithmique simple)
        bonus_commandes = min(plat.nombre_commandes * 1.5, 20.0)
        bonus_likes = min(plat.nombre_likes * 0.5, 10.0)
        score += bonus_commandes + bonus_likes

        if bonus_commandes >= 10.0 and not raisons:
            raisons.append("Très populaire auprès des gourmets dakarois")

        raison_finale = raisons[0] if raisons else "Sélection gourmande AYYOU"
        scores_plats.append((score, plat, raison_finale))

    # Trier par score décroissant
    scores_plats.sort(key=lambda item: item[0], reverse=True)

    resultats: List[PlatRecommande] = []
    for score, plat, raison in scores_plats[: requete.limite]:
        resultats.append(
            PlatRecommande(
                id=plat.id,
                nom=plat.nom,
                nom_restaurant=plat.nom_restaurant,
                prix_fcfa=plat.prix_fcfa,
                score_pertinence=round(score, 1),
                raison_recommandation=raison,
            )
        )

    return ReponseRecommandation(
        recommandations=resultats,
        contexte_moment=moment_nom,
        total=len(resultats),
    )
