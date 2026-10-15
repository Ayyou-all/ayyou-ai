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
    if requete.taux_acceptation_pourcent >= 95.0:
        points_forts.append(f"Excellente réactivité : taux d'acceptation de {requete.taux_acceptation_pourcent}% des commandes.")
    if requete.temps_moyen_preparation_minutes <= 25:
        points_forts.append(f"Vitesse de préparation remarquable ({requete.temps_moyen_preparation_minutes} min en moyenne).")
    if panier_moyen >= 4500:
        points_forts.append(f"Panier moyen élevé ({panier_moyen:,} FCFA), signe d'un menu bien valorisé.")
    if not points_forts:
        points_forts.append("Activité constante sur la plateforme AYYOU.")

    # Recommandations concrètes
    recommandations = []
    if requete.temps_moyen_preparation_minutes > 30:
        recommandations.append(
            "Réduisez le temps d'attente des livreurs au comptoir en pré-emballant les sauces et couverts à l'avance."
        )
    if requete.plats_vendus and len(requete.plats_vendus) >= 3:
        recommandations.append(
            f"Mettez en avant le plat vedette '{plat_star.split('(')[0].strip()}' dans une courte vidéo Reels de 30 secondes pour booster vos vues."
        )
    recommandations.append(
        "Proposez des formules combinées (plat + boisson locale Bissap/Bouye) pour faire progresser votre panier moyen de 15%."
    )

    resume = (
        f"Cette semaine, {requete.nom_restaurant} a traité {total_cmd} commandes pour un chiffre d'affaires total "
        f"de {ca:,} FCFA (panier moyen : {panier_moyen:,} FCFA). La régularité de votre brigade permet de fidéliser "
        "votre clientèle dakaroise."
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
