"""
Moteur de prévisions de flux et tendances restaurant AYYOU.
Permet au gérant d'anticiper les coups de feu en cuisine et d'optimiser ses stocks.
"""

from typing import List
from ..schemas.previsions import (
    PrevisionHeure,
    ReponsePrevisions,
    RequetePrevisions,
)


def calculer_previsions_flux(requete: RequetePrevisions) -> ReponsePrevisions:
    jour = requete.jour_cible  # 0=Lundi, 4=Vendredi, 5=Samedi, 6=Dimanche

    # Multiplicateur selon le jour à Dakar (le vendredi et le week-end connaissent une hausse)
    facteurs_jours = {
        0: 0.85,  # Lundi plus calme
        1: 0.90,  # Mardi
        2: 0.95,  # Mercredi
        3: 1.00,  # Jeudi
        4: 1.35,  # Vendredi (jour du grand Thieb de midi et sorties du soir)
        5: 1.40,  # Samedi (fortes commandes familiales et dîners)
        6: 1.25,  # Dimanche (déjeuners de fête)
    }
    facteur_jour = facteurs_jours.get(jour, 1.0)

    # Profil horaire standard (heures 10h à 23h)
    profil_de_base = {
        10: 2,
        11: 5,
        12: 18,  # Début coup de feu déjeuner
        13: 25,  # Pic déjeuner
        14: 15,
        15: 4,
        16: 3,
        17: 4,
        18: 6,
        19: 12,
        20: 22,  # Pic dîner
        21: 26,  # Pic dîner
        22: 14,
        23: 5,
    }

    # Si un historique est fourni, ajuster avec la moyenne observée
    ajustement_historique = 1.0
    if requete.historique_ventes:
        total_historique = sum(v.quantite_commandes for v in requete.historique_ventes if v.jour_semaine == jour)
        if total_historique > 0:
            ajustement_historique = max(total_historique / 150.0, 0.5)

    previsions: List[PrevisionHeure] = []
    max_commandes = 0
    heure_pic = 13

    for h, base in profil_de_base.items():
        commandes = int(base * facteur_jour * ajustement_historique)
        if commandes > max_commandes:
            max_commandes = commandes
            heure_pic = h

        if commandes >= 20:
            intensite = "COUP_DE_FEU"
        elif commandes >= 8:
            intensite = "MODÉRÉ"
        else:
            intensite = "CALME"

        previsions.append(
            PrevisionHeure(
                heure=h,
                commandes_estimees=commandes,
                intensite=intensite,
            )
        )

    # Conseils organisationnels ciblés
    conseils = [
        f"Préparez le conditionnement et les barquettes dès {heure_pic - 1}h pour fluidifier les départs livreurs.",
        "Assurez une mise en place complète des sauces et accompagnements avant 11h30.",
    ]
    if jour == 4:
        conseils.append("Vendredi : pic important de commandes de Thiéboudienne attendu entre 12h30 et 14h00.")
    elif jour in (5, 6):
        conseils.append("Week-end : renforcez l'équipe de conditionnement pour réduire le temps de remise au guichet.")

    return ReponsePrevisions(
        restaurant_id=requete.restaurant_id,
        nom_restaurant=requete.nom_restaurant,
        previsions_par_heure=previsions,
        heure_de_pointe=f"{heure_pic}h00 - {heure_pic + 1}h00 (~{max_commandes} commandes)",
        conseils_organisation=conseils,
    )
