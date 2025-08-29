#!/bin/bash

# Script de démarrage avec protection des tokens
# Utilise le gestionnaire de tokens pour sauvegarder et restaurer

echo "==========================================="
echo "🚀 Démarrage C2B Heritage avec Protection"
echo "==========================================="

# Déterminer l'environnement
if [ "$RENDER" = "true" ]; then
    echo "📍 Environnement: Render"
    DATA_DIR="/opt/render/project/data"
else
    echo "📍 Environnement: Local"
    DATA_DIR="data"
fi

# Créer les répertoires nécessaires
mkdir -p $DATA_DIR
mkdir -p $DATA_DIR/backups
mkdir -p files

# Backup des tokens existants
echo ""
echo "🔐 Sauvegarde des tokens..."
python3 token_manager.py backup 2>/dev/null || echo "Première exécution - pas de tokens à sauvegarder"

# Initialiser les bases de données si nécessaire
echo ""
echo "📊 Vérification des bases de données..."

# Heritage
if [ ! -f "$DATA_DIR/soumissions_heritage.db" ]; then
    echo "Création de la base Heritage..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('$DATA_DIR/soumissions_heritage.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS soumissions_heritage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE NOT NULL,
        client_nom TEXT,
        projet_nom TEXT,
        montant_total REAL,
        statut TEXT DEFAULT 'en_attente',
        token TEXT UNIQUE,
        data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('✅ Base Heritage créée')
"
fi

# Multi-format
if [ ! -f "$DATA_DIR/soumissions_multi.db" ]; then
    echo "Création de la base Multi-format..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('$DATA_DIR/soumissions_multi.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS soumissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_soumission TEXT UNIQUE NOT NULL,
        nom_client TEXT NOT NULL,
        email_client TEXT,
        telephone_client TEXT,
        nom_projet TEXT NOT NULL,
        description_projet TEXT,
        montant_total REAL,
        file_path TEXT,
        file_type TEXT,
        file_size INTEGER,
        file_name TEXT,
        file_data BLOB,
        statut TEXT DEFAULT 'en_attente',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_decision TIMESTAMP,
        commentaire_client TEXT,
        token TEXT UNIQUE,
        lien_public TEXT
    )
''')
conn.commit()
conn.close()
print('✅ Base Multi-format créée')
"
fi

# Restaurer les tokens si nécessaire
echo ""
echo "🔄 Restauration des tokens..."
python3 token_manager.py restore 2>/dev/null || echo "Pas de tokens à restaurer"

# Générer les tokens manquants
echo ""
echo "🔑 Génération des tokens manquants..."
python3 token_manager.py generate 2>/dev/null || echo "Tous les tokens sont présents"

# Afficher les statistiques
echo ""
echo "📊 Statistiques:"
python3 token_manager.py stats 2>/dev/null || echo "Impossible d'obtenir les statistiques"

# Nettoyer l'espace disque si sur Render
if [ "$RENDER" = "true" ]; then
    echo ""
    echo "💾 Espace disque:"
    df -h $DATA_DIR | tail -1
    
    USAGE=$(df $DATA_DIR | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$USAGE" -gt 80 ]; then
        echo "⚠️ Espace disque élevé (${USAGE}%) - Nettoyage..."
        python3 token_manager.py clean 7 2>/dev/null
        find $DATA_DIR/backups -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
        echo "✅ Nettoyage effectué"
    fi
fi

echo ""
echo "==========================================="
echo "✅ Initialisation terminée"
echo "==========================================="
echo ""

# Lancer Streamlit
if [ "$RENDER" = "true" ]; then
    streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
else
    streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0
fi