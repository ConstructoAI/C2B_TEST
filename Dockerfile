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
RUN mkdir -p data files data/backups && \
    chmod -R 777 data files data/backups

# Rendre les scripts d'initialisation exécutables
RUN chmod +x init_render.sh || true
RUN chmod +x init_render_safe.sh || true
RUN chmod +x startup.sh || true
RUN chmod +x clean_disk_render.sh || true
RUN chmod +x fix_file_paths.py || true
RUN chmod +x fix_client_links.py || true
RUN chmod +x token_manager.py || true

# Variable d'environnement pour le port
ENV PORT=8501

# Exposer le port
EXPOSE $PORT

# Commande de démarrage
# Utilise le nouveau script startup.sh avec protection des tokens
CMD if [ -f "./startup.sh" ]; then \
        ./startup.sh; \
    elif [ "$RENDER" = "true" ] && [ -f "./init_render.sh" ]; then \
        ./init_render.sh; \
    else \
        streamlit run app.py \
        --server.port=$PORT \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --browser.gatherUsageStats=false \
        --server.enableCORS=false; \
    fi