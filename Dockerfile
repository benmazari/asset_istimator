FROM python:3.10-slim

# Eviter l'écriture de fichiers .pyc en cache et forcer l'affichage immédiat des logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Installation des dépendances système nécessaires pour psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste des fichiers de l'application
COPY . .

# Création du dossier de sortie par défaut
RUN mkdir -p output

# Exposition du port
EXPOSE 5000

# Démarrage de l'application en mode production via Waitress
CMD ["waitress-serve", "--host=0.0.0.0", "--port=5000", "ui:app"]
