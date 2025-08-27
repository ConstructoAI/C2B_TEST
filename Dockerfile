FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY . .

# Créer les dossiers nécessaires avec les bonnes permissions
RUN mkdir -p data files && \
    chmod -R 777 data files

# Rendre le script d'initialisation exécutable
RUN chmod +x init_render.sh

# Variable d'environnement pour le port
ENV PORT=8501

# Exposer le port
EXPOSE $PORT

# Commande de démarrage
# Utilise le script d'initialisation si on est sur Render, sinon commande normale
CMD if [ "$RENDER" = "true" ]; then \
        ./init_render.sh; \
    else \
        streamlit run app.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false \
        --server.enableCORS=false; \
    fi