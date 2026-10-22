"""
Point d'entrée du Microservice d'Intelligence Artificielle AYYOU.

Fournit les capacités IA FoodTech :
1. Transcription vocale haute précision (Speech-to-Text avec Whisper)
2. Chatbot culinaire conversationnel sous contrainte budgétaire stricte (LLM)
3. Recherche vocale intelligente (phrase dictée -> filtres de recherche)
4. Recommandations contextualisées de plats réels
"""

import sys
from pathlib import Path
from fastapi import FastAPI  # pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware  # pyrefly: ignore [missing-import]

# Configuration des chemins système pour exécution autonome ou via module
dossier_ia = Path(__file__).resolve().parent
racine_projet = dossier_ia.parent

for chemin in (str(dossier_ia), str(racine_projet)):
    if chemin not in sys.path:
        sys.path.insert(0, chemin)

try:
    from ayyouServiceIA.config import parametres  # pyrefly: ignore [missing-import]
    from ayyouServiceIA.routes import (  # pyrefly: ignore [missing-import]
        chatbot,
        recherche_vocale,
        recommandations,
        sante,
        transcription,
    )
except (ImportError, ModuleNotFoundError):
    from config import parametres  # pyrefly: ignore [missing-import]
    from routes import (  # pyrefly: ignore [missing-import]
        chatbot,
        recherche_vocale,
        recommandations,
        sante,
        transcription,
    )

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

# Inclusion des routeurs actifs : Whisper, Chatbot Culinaire sous budget, Recherche vocale, Recommandations
app.include_router(sante.routeur)
app.include_router(transcription.routeur)
app.include_router(chatbot.routeur)
app.include_router(recherche_vocale.routeur)
app.include_router(recommandations.routeur)


@app.on_event("startup")
def precharger_whisper():
    """Pré-charge le modèle Whisper en mémoire dès le lancement du serveur."""
    try:
        from services.moteur_transcription import obtenir_pipeline_whisper
        obtenir_pipeline_whisper()
    except Exception:
        try:
            from ayyouServiceIA.services.moteur_transcription import obtenir_pipeline_whisper
            obtenir_pipeline_whisper()
        except Exception:
            pass


@app.get("/", tags=["Supervision"])
def racine():
    return {
        "message": "Bienvenue sur le service IA d'AYYOU.",
        "docs": "/docs",
        "statut": "actif",
        "service": parametres.NOM_SERVICE,
        "version": parametres.VERSION,
    }


@app.get("/sante", tags=["Supervision"])
@app.get("/sante/", tags=["Supervision"])
def verifier_etat_sante():
    return {
        "statut": "OK",
        "service": parametres.NOM_SERVICE,
        "version": parametres.VERSION,
    }

if __name__ == "__main__":
    # pyrefly: ignore[missing-import]
    import uvicorn
    uvicorn.run("main:app", host=parametres.HOTE, port=parametres.PORT, reload=True)
