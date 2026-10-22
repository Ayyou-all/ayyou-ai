"""
Moteur de transcription vocale AYYOU (Speech-to-Text avec Whisper).
Transcrit les enregistrements audio (WebM, WAV, OGG, MP3) en texte pour :
1. Le chatbot culinaire (notes vocales dans le chat)
2. La barre de recherche catalogue (recherche vocale)
"""

import logging
import os
import tempfile
from typing import Optional

logger = logging.getLogger("ayyou.ia.whisper")

_pipeline_whisper = None


def obtenir_pipeline_whisper():
    """Charge le modèle Whisper local (openai/whisper-base) avec optimisation CPU multithread."""
    global _pipeline_whisper
    if _pipeline_whisper is None:
        try:
            import torch
            # Exploiter tous les cœurs logiques CPU disponibles
            nb_coeurs = os.cpu_count() or 4
            torch.set_num_threads(nb_coeurs)

            from transformers import pipeline
            logger.info("Chargement du modèle Whisper base...")
            _pipeline_whisper = pipeline(
                "automatic-speech-recognition",
                model="openai/whisper-base",
                device="cpu",
            )
            logger.info("Modèle Whisper base prêt !")
        except Exception as exc:
            logger.error("Impossible d'initialiser le modèle Whisper : %s", exc)
            return None
    return _pipeline_whisper


def transcrire_audio(donnees_audio: bytes, nom_fichier: str = "audio.webm") -> dict:
    """
    Transcrit un flux binaire audio en texte.
    Supporte les formats WebM, WAV, OGG, MP3 générés par le navigateur.
    """
    if not donnees_audio or len(donnees_audio) < 100:
        return {
            "succes": False,
            "texte": "",
            "message": "Le fichier audio est vide ou trop court.",
        }

    # Détermination de l'extension
    suffixe = ".webm"
    if nom_fichier:
        _, ext = os.path.splitext(nom_fichier)
        if ext.lower() in [".wav", ".ogg", ".mp3", ".m4a", ".webm"]:
            suffixe = ext.lower()

    fichier_temp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffixe, delete=False) as f:
            f.write(donnees_audio)
            fichier_temp = f.name

        asr = obtenir_pipeline_whisper()
        if asr is None:
            return {
                "succes": False,
                "texte": "",
                "message": "Le moteur de transcription Whisper n'est pas disponible.",
            }

        resultat = asr(
            fichier_temp,
            chunk_length_s=30,
            generate_kwargs={"language": "french", "task": "transcribe", "max_new_tokens": 96},
        )
        texte = (resultat.get("text") or "").strip()

        return {
            "succes": True,
            "texte": texte,
            "modele": "openai/whisper-base",
        }

    except Exception as exc:
        logger.exception("Erreur lors de la transcription Whisper : %s", exc)
        return {
            "succes": False,
            "texte": "",
            "message": f"Erreur de transcription : {str(exc)}",
        }
    finally:
        if fichier_temp and os.path.exists(fichier_temp):
            try:
                os.remove(fichier_temp)
            except OSError:
                pass
