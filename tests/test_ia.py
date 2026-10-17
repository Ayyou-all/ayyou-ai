"""
Tests automatisés pour le microservice FastAPI AYYOU IA.

Scénarios validés :
1. Route de santé publique sans authentification.
2. Sécurité interne : rejet 403 si en-tête X-AYYOU-IA-KEY manquant ou incorrect.
3. Recommandations déterministes : filtrage budget, bonus temporel, tri score.
4. Chatbot gourmand : extraction de budget et matching de plats réels.
5. Prévisions de flux : identification du coup de feu.
6. Rapport hebdomadaire : calcul panier moyen et plat vedette.
"""

from fastapi.testclient import TestClient
import pytest

from ayyouServiceIA.main import app
from ayyouServiceIA.config import parametres

client = TestClient(app)
EN_TETE_AUTH = {"X-AYYOU-IA-KEY": parametres.CLE_SECRETE_INTERNE}


def test_route_sante_publique():
    rep = client.get("/ia/sante/")
    assert rep.status_code == 200
    assert rep.json()["statut"] == "OK"


def test_securite_rejet_cle_invalide():
    # 1. Sans header
    rep1 = client.post("/ia/recommandations/", json={"plats": []})
    assert rep1.status_code == 422 or rep1.status_code == 403

    # 2. Mauvaise clé
    rep2 = client.post(
        "/ia/recommandations/",
        json={"plats": []},
        headers={"X-AYYOU-IA-KEY": "cle-pirate-invalide"},
    )
    assert rep2.status_code == 403


def test_recommandations_avec_budget_et_heure():
    payload = {
        "plats": [
            {
                "id": 1,
                "nom": "Thiéboudienne Rouge Penda Mbaye",
                "description": "Riz rouge au mérou",
                "prix_fcfa": 3500,
                "restaurant_id": 10,
                "nom_restaurant": "Chez Loutcha",
                "categorie": "Plats traditionnels",
                "nombre_likes": 15,
                "nombre_commandes": 50,
            },
            {
                "id": 2,
                "nom": "Homard Royal Braisé",
                "description": "Fruits de mer",
                "prix_fcfa": 15000,
                "restaurant_id": 11,
                "nom_restaurant": "Alkimia",
                "categorie": "Luxe",
                "nombre_likes": 100,
                "nombre_commandes": 20,
            },
            {
                "id": 3,
                "nom": "Dibi Agneau Dakar",
                "description": "Viande grillée au feu de bois",
                "prix_fcfa": 4000,
                "restaurant_id": 12,
                "nom_restaurant": "Dibiterie Haoussa",
                "categorie": "Grillades",
                "nombre_likes": 30,
                "nombre_commandes": 40,
            },
        ],
        "budget_max_fcfa": 5000,
        "heure_actuelle": 13,  # Midi
        "limite": 5,
    }

    rep = client.post("/ia/recommandations/", json=payload, headers=EN_TETE_AUTH)
    assert rep.status_code == 200
    data = rep.json()
    assert data["total"] == 2  # Le homard à 15 000 FCFA est exclu par le budget
    assert data["contexte_moment"] == "Déjeuner traditionnel de midi"

    # Le thieb de midi doit être premier grâce au bonus temporel
    assert data["recommandations"][0]["id"] == 1
    assert data["recommandations"][0]["prix_fcfa"] <= 5000


def test_chatbot_comprehension_budget():
    payload = {
        "message": "Bonjour, j'ai 3000 fcfa, que me conseillez-vous pour manger ce midi ?",
        "plats_disponibles": [
            {
                "id": 101,
                "nom": "Yassa Poulet Fermier",
                "prix_fcfa": 2500,
                "restaurant_id": 5,
                "nom_restaurant": "Le Teranga",
                "nombre_likes": 10,
                "nombre_commandes": 20,
            },
            {
                "id": 102,
                "nom": "Plateau Grillades Mixtes",
                "prix_fcfa": 7500,
                "restaurant_id": 5,
                "nom_restaurant": "Le Teranga",
                "nombre_likes": 50,
                "nombre_commandes": 30,
            },
        ],
    }

    rep = client.post("/ia/chatbot/", json=payload, headers=EN_TETE_AUTH)
    assert rep.status_code == 200
    data = rep.json()
    assert data["budget_respecte"] is True
    assert 101 in data["plats_suggeres_ids"]
    assert 102 not in data["plats_suggeres_ids"]  # 7500 > 3000
    assert "Yassa Poulet Fermier" in data["texte_reponse"]


def test_previsions_calculees_sur_l_historique():
    # 4 vendredis : 8 commandes à 13h et 2 à 10h au total
    payload = {
        "restaurant_id": 1,
        "nom_restaurant": "Chez Loutcha",
        "jour_cible": 4,
        "nombre_semaines": 4,
        "historique_ventes": [
            {"jour_semaine": 4, "heure": 13, "quantite_commandes": 8},
            {"jour_semaine": 4, "heure": 10, "quantite_commandes": 2},
            {"jour_semaine": 1, "heure": 12, "quantite_commandes": 40},  # mardi : ignoré
        ],
    }
    rep = client.post("/ia/previsions/", json=payload, headers=EN_TETE_AUTH)
    assert rep.status_code == 200
    data = rep.json()
    assert [(p["heure"], p["commandes_estimees"]) for p in data["previsions_par_heure"]] == [(10, 0.5), (13, 2.0)]
    assert data["previsions_par_heure"][1]["intensite"] == "COUP_DE_FEU"
    assert data["heure_de_pointe"].startswith("13h")


def test_previsions_sans_historique_n_inventent_rien():
    payload = {"restaurant_id": 1, "nom_restaurant": "Chez Loutcha", "jour_cible": 4}
    data = client.post("/ia/previsions/", json=payload, headers=EN_TETE_AUTH).json()
    assert data["previsions_par_heure"] == []
    assert data["heure_de_pointe"] == ""


def test_rapport_hebdomadaire():
    payload = {
        "restaurant_id": 1,
        "nom_restaurant": "Chez Loutcha",
        "total_commandes": 120,
        "chiffre_affaires_fcfa": 420000,
        "plats_vendus": [
            {"nom": "Thiéboudienne Penda Mbaye", "quantite": 85, "chiffre_affaires_fcfa": 297500},
            {"nom": "Yassa Poisson", "quantite": 35, "chiffre_affaires_fcfa": 122500},
        ],
        "taux_acceptation_pourcent": 98.0,
        "temps_moyen_preparation_minutes": 22,
    }

    rep = client.post("/ia/rapport/", json=payload, headers=EN_TETE_AUTH)
    assert rep.status_code == 200
    data = rep.json()
    assert data["panier_moyen_fcfa"] == 3500  # 420000 / 120
    assert "Thiéboudienne Penda Mbaye" in data["plat_star"]
    assert len(data["points_forts"]) >= 1


def test_rapport_sans_metriques_connues():
    payload = {"restaurant_id": 1, "nom_restaurant": "Chez Loutcha", "total_commandes": 6, "chiffre_affaires_fcfa": 18000,
               "taux_acceptation_pourcent": 80.0}
    data = client.post("/ia/rapport/", json=payload, headers=EN_TETE_AUTH).json()
    assert data["panier_moyen_fcfa"] == 3000
    assert any("80.0%" in r for r in data["recommandations_actionnables"])
