"""
Moteur de prévisions de flux et tendances restaurant AYYOU.
Permet au gérant d'anticiper les coups de feu en cuisine et d'optimiser ses stocks.
"""

from typing import List

try:
    from ..schemas.previsions import (
        PrevisionHeure,
        ReponsePrevisions,
        RequetePrevisions,
    )
except (ImportError, ValueError):
    try:
        from schemas.previsions import (
            PrevisionHeure,
            ReponsePrevisions,
            RequetePrevisions,
        )
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.previsions import (
            PrevisionHeure,
            ReponsePrevisions,
            RequetePrevisions,
        )


def calculer_previsions_flux(requete: RequetePrevisions) -> ReponsePrevisions:
    """
    Prévision heure par heure pour `jour_cible` = moyenne des commandes observées
    ce même jour de la semaine sur l'historique fourni (ex. : 4 derniers vendredis).
    Aucune courbe « type » inventée : une heure sans historique n'apparaît pas.
    """
    ventes_du_jour = [v for v in requete.historique_ventes if v.jour_semaine == requete.jour_cible]

    previsions: List[PrevisionHeure] = []
    for vente in sorted(ventes_du_jour, key=lambda v: v.heure):
        moyenne = round(vente.quantite_commandes / requete.nombre_semaines, 1)
        previsions.append(PrevisionHeure(heure=vente.heure, commandes_estimees=moyenne, intensite=""))

    # Intensité relative au pic de la journée (le pic = « COUP_DE_FEU »)
    pic = max((p.commandes_estimees for p in previsions), default=0)
    for prevision in previsions:
        if pic and prevision.commandes_estimees >= 0.7 * pic:
            prevision.intensite = "COUP_DE_FEU"
        elif pic and prevision.commandes_estimees >= 0.35 * pic:
            prevision.intensite = "MODÉRÉ"
        else:
            prevision.intensite = "CALME"

    heure_pic = max(previsions, key=lambda p: p.commandes_estimees).heure if previsions else None
    conseils = []
    if heure_pic is not None:
        conseils.append(
            f"Votre pic habituel ce jour-là est vers {heure_pic}h : préparez emballages et mise en place avant {heure_pic - 1}h."
        )

    return ReponsePrevisions(
        restaurant_id=requete.restaurant_id,
        nom_restaurant=requete.nom_restaurant,
        previsions_par_heure=previsions,
        heure_de_pointe=f"{heure_pic}h00 - {heure_pic + 1}h00 (~{pic} commandes)" if heure_pic is not None else "",
        conseils_organisation=conseils,
    )
