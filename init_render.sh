#!/bin/bash

# Script d'initialisation pour Render avec disque persistant

echo "=========================================="
echo "Initialisation C2B Heritage sur Render"
echo "=========================================="

# Vérifier l'espace disque disponible
echo "💾 Espace disque:"
df -h /opt/render/project/data | tail -1

# Nettoyer les vieux backups si l'espace est limité
USAGE=$(df /opt/render/project/data | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 80 ]; then
    echo "⚠️ Espace disque utilisé à ${USAGE}% - Nettoyage des vieux backups..."
    find /opt/render/project/data -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
    echo "✅ Backups de plus de 7 jours supprimés"
fi

# Créer le répertoire data s'il n'existe pas
if [ ! -d "/opt/render/project/data" ]; then
    echo "Création du répertoire /opt/render/project/data..."
    mkdir -p /opt/render/project/data
fi

# Créer un lien symbolique si on n'est pas déjà dans le bon répertoire
if [ "$PWD" != "/opt/render/project/src" ]; then
    # Si le lien symbolique n'existe pas, le créer
    if [ ! -L "data" ]; then
        # Supprimer le dossier data local s'il existe et n'est pas un lien
        if [ -d "data" ] && [ ! -L "data" ]; then
            echo "Suppression du dossier data local..."
            rm -rf data
        fi
        
        echo "Création du lien symbolique vers /opt/render/project/data..."
        ln -s /opt/render/project/data data
    fi
fi

# Vérifier que les bases de données existent, sinon les créer
if [ ! -f "/opt/render/project/data/soumissions_heritage.db" ]; then
    echo "Initialisation de la base de données Heritage..."
    python -c "
import sqlite3
conn = sqlite3.connect('/opt/render/project/data/soumissions_heritage.db')
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
print('Base de données Heritage créée avec succès!')
"
fi

if [ ! -f "/opt/render/project/data/soumissions_multi.db" ]; then
    echo "Initialisation de la base de données Multi-format..."
    python -c "
import sqlite3
conn = sqlite3.connect('/opt/render/project/data/soumissions_multi.db')
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
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_size INTEGER,
        file_name TEXT,
        statut TEXT DEFAULT 'en_attente',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_decision TIMESTAMP,
        commentaire_client TEXT,
        token TEXT UNIQUE NOT NULL,
        lien_public TEXT
    )
''')
conn.commit()
conn.close()
print('Base de données Multi-format créée avec succès!')
"
fi

echo "Initialisation terminée!"
echo ""
echo "📊 Statistiques:"
# Compter les soumissions
if [ -f "/opt/render/project/data/soumissions_heritage.db" ]; then
    HERITAGE_COUNT=$(sqlite3 /opt/render/project/data/soumissions_heritage.db "SELECT COUNT(*) FROM soumissions_heritage" 2>/dev/null || echo "0")
    echo "  - Soumissions Heritage: $HERITAGE_COUNT"
fi
if [ -f "/opt/render/project/data/soumissions_multi.db" ]; then
    MULTI_COUNT=$(sqlite3 /opt/render/project/data/soumissions_multi.db "SELECT COUNT(*) FROM soumissions" 2>/dev/null || echo "0")
    echo "  - Soumissions Multi-format: $MULTI_COUNT"
fi

echo ""
echo "📁 Fichiers dans /opt/render/project/data:"
ls -lah /opt/render/project/data/ | head -20

echo ""
echo "💾 Espace disque final:"
df -h /opt/render/project/data | tail -1

echo ""
echo "=========================================="
echo "✅ Prêt à démarrer l'application"
echo "=========================================="
echo ""

# Lancer l'application
streamlit run app.py --server.port=$PORT --server.address=0.0.0.0