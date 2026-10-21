"""
Point d'entrée du Microservice d'Intelligence Artificielle AYYOU.

Fournit 5 capacités IA spécialisées FoodTech :
1. Recommandations déterministes contextualisées (affinité, heure, Dakar)
2. Chatbot culinaire sous budget avec cartes de plats réels cliquables
3. Prévisions de flux et coups de feu en cuisine
4. Rapport managérial hebdomadaire pour les gérants
5. Recherche vocale intelligente (phrase dictée -> filtres de recherche)
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Assure que le microservice IA peut être lancé directement via `uvicorn main:app` ou `uvicorn ayyouServiceIA.main:app`
dossier_ia = Path(__file__).resolve().parent
racine_projet = dossier_ia.parent

for chemin in (str(dossier_ia), str(racine_projet)):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)


try:
    from ayyouServiceIA.config import parametres
    from ayyouServiceIA.routes import chatbot, previsions, rapport, recherche_vocale, recommandations, sante
except ImportError:
    try:
        from .config import parametres
        from .routes import chatbot, previsions, rapport, recherche_vocale, recommandations, sante
    except ImportError:
        from config import parametres
        from routes import chatbot, previsions, rapport, recherche_vocale, recommandations, sante

app = FastAPI(
    title=parametres.NOM_SERVICE,
    version=parametres.VERSION,
    description="Microservice indépendant d'IA culinaire pour la plateforme AYYOU Sénégal.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(sante.routeur)
app.include_router(recommandations.routeur)
app.include_router(chatbot.routeur)
app.include_router(previsions.routeur)
app.include_router(rapport.routeur)
app.include_router(recherche_vocale.routeur)


@app.get("/")
def racine():
    return {
        "message": "Bienvenue sur le service IA d'AYYOU.",
        "docs": "/docs",
        "statut": "actif",
    }


@app.get("/sante")
def sante():
    return {"statut": "OK", "service": parametres.NOM_SERVICE, "version": parametres.VERSION}
