FROM python:3.12-slim

# Optimisation Python et configuration du PYTHONPATH
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Installation des dépendances système légères (curl et ffmpeg pour Whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances du microservice IA
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source du service IA
COPY . .

# Lien symbolique pour compatibilité native avec 'import ayyouServiceIA'
RUN ln -s /app /app/ayyouServiceIA 2>/dev/null || true

# Vérification de santé du service IA
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/sante || exit 1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
