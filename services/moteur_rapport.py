"""
Moteur de génération du rapport hebdomadaire pour les gérants AYYOU.
Analyse les performances commerciales, la rapidité en cuisine et formule des recommandations.
"""

try:
    from ..schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
except (ImportError, ValueError):
    try:
        from schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo
    except (ImportError, ValueError):
        from ayyouServiceIA.schemas.rapport import ReponseRapportHebdo, RequeteRapportHebdo


def generer_rapport_hebdomadaire(requete: RequeteRapportHebdo) -> ReponseRapportHebdo:
    total_cmd = requete.total_commandes
    ca = requete.chiffre_affaires_fcfa
    panier_moyen = int(ca / total_cmd) if total_cmd > 0 else 0

    # Déterminer le plat star
    if requete.plats_vendus:
        plat_star_obj = max(requete.plats_vendus, key=lambda p: p.quantite)
        plat_star = f"{plat_star_obj.nom} ({plat_star_obj.quantite} commandes)"
    else:
        plat_star = "Aucune vente enregistrée cette semaine"

    # Points forts
    points_forts = []
    taux = requete.taux_acceptation_pourcent
    temps = requete.temps_moyen_preparation_minutes
    if taux is not None and taux >= 95.0:
        points_forts.append(f"Excellente réactivité : taux d'acceptation de {taux}% des commandes.")
    if temps is not None and temps <= 25:
        points_forts.append(f"Vitesse de préparation remarquable ({temps} min en moyenne).")
    if panier_moyen >= 4500:
        points_forts.append(f"Panier moyen élevé ({panier_moyen:,} FCFA), signe d'un menu bien valorisé.")

    # Recommandations concrètes
    recommandations = []
    if temps is not None and temps > 30:
        recommandations.append(
            "Réduisez le temps d'attente des livreurs au comptoir en pré-emballant les sauces et couverts à l'avance."
        )
    if requete.plats_vendus and len(requete.plats_vendus) >= 3:
        recommandations.append(
            f"Mettez en avant le plat vedette '{plat_star.split('(')[0].strip()}' dans une courte vidéo Reels de 30 secondes pour booster vos vues."
        )
    if taux is not None and taux < 90:
        recommandations.append(
            f"Votre taux d'acceptation est de {taux}% : fermez le restaurant dans l'application quand vous ne pouvez pas servir."
        )

    resume = (
        f"Cette semaine, {requete.nom_restaurant} a traité {total_cmd} commandes pour un chiffre d'affaires total "
        f"de {ca:,} FCFA (panier moyen : {panier_moyen:,} FCFA)."
    )

    return ReponseRapportHebdo(
        restaurant_id=requete.restaurant_id,
        titre_rapport=f"Bilan de performance hebdomadaire — {requete.nom_restaurant}",
        resume_executif=resume,
        plat_star=plat_star,
        panier_moyen_fcfa=panier_moyen,
        points_forts=points_forts,
        recommandations_actionnables=recommandations,
    )
