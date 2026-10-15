# Microservice IA Indépendant — AYYOU Sénégal 🇸🇳

Microservice d'intelligence artificielle dédié aux plateformes FoodTech et marketplaces culinaires, développé avec **FastAPI**.

## Capacités & Endpoints

1. **`GET /ia/sante/`** : Point de contrôle de disponibilité du microservice (supervision Kubernetes, Docker, uptime).
2. **`POST /ia/recommandations/`** : Algorithme déterministe de suggestion de plats basé sur l'affinité du client, l'heure locale à Dakar et le budget.
3. **`POST /ia/chatbot/`** : Moteur conversationnel analysant les demandes en langage naturel sous budget et suggérant des plats réels cliquables.
4. **`POST /ia/previsions/`** : Estimations de flux horaire de commandes pour aider les restaurants à gérer leurs coups de feu et leurs brigades.
5. **`POST /ia/rapport/`** : Rapport hebdomadaire managérial synthétisant le panier moyen, le plat star et les recommandations d'approvisionnement.

## Sécurisation Interne

Ce microservice n'est pas exposé directement aux clients finaux.
Chaque requête doit provenir du backend Django via l'en-tête HTTP :
```http
X-AYYOU-IA-KEY: cle-secrete-interne-ayyou-ia-2026
```

## Démarrage Local

```bash
uvicorn ayyouServiceIA.main:app --host 127.0.0.1 --port 8001 --reload
```
Documentation Swagger OpenAPI interactive disponible sur : `http://127.0.0.1:8001/docs`.
