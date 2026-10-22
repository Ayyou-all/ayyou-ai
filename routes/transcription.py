"""
Route de transcription vocale Whisper : fichier audio / base64 -> texte transcrit.
"""

import base64
from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile  # pyrefly: ignore [missing-import]
from pydantic import BaseModel  # pyrefly: ignore [missing-import]

try:
    from ..securite import verifier_cle_ia
    from ..services.moteur_transcription import transcrire_audio
except (ImportError, ValueError):
    try:
        from securite import verifier_cle_ia  # pyrefly: ignore [missing-import]
        from services.moteur_transcription import transcrire_audio  # pyrefly: ignore [missing-import]
    except (ImportError, ValueError):
        from ayyouServiceIA.securite import verifier_cle_ia  # pyrefly: ignore [missing-import]
        from ayyouServiceIA.services.moteur_transcription import transcrire_audio  # pyrefly: ignore [missing-import]

routeur = APIRouter(prefix="/ia/transcription", tags=["Transcription Vocale"])


class RequeteTranscriptionBase64(BaseModel):
    audio_base64: str
    nom_fichier: Optional[str] = "audio.webm"


@routeur.post("/", dependencies=[Depends(verifier_cle_ia)])
def transcrire_fichier(fichier: UploadFile = File(...)):
    """Transcrit un fichier audio envoyé en multipart/form-data."""
    contenu = fichier.file.read()
    return transcrire_audio(contenu, nom_fichier=fichier.filename or "audio.webm")


@routeur.post("/base64/", dependencies=[Depends(verifier_cle_ia)])
def transcrire_base64(requete: RequeteTranscriptionBase64):
    """Transcrit des données audio encodées en base64."""
    donnees = base64.b64decode(requete.audio_base64)
    return transcrire_audio(donnees, nom_fichier=requete.nom_fichier or "audio.webm")
