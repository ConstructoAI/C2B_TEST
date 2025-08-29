#!/bin/bash

# Script d'initialisation pour Render avec disque persistant et protection des tokens

echo "=========================================="
echo "Initialisation C2B Heritage sur Render"
echo "Version avec Protection des Tokens"
echo "=========================================="

# Vérifier l'espace disque disponible
echo "💾 Espace disque:"
df -h /opt/render/project/data | tail -1

# NOUVEAU: Sauvegarde des tokens avant toute modification
echo ""
echo "🔐 Sauvegarde des tokens existants..."
python3 -c "
import sqlite3
import json
from datetime import datetime
import os

tokens_to_save = []
backup_dir = '/opt/render/project/data/backups'
os.makedirs(backup_dir, exist_ok=True)

# Sauvegarder depuis Heritage
if os.path.exists('data/soumissions_heritage.db'):
    try:
        conn = sqlite3.connect('data/soumissions_heritage.db')
        cursor = conn.cursor()
        cursor.execute('SELECT numero, client_nom, token, created_at FROM soumissions_heritage WHERE token IS NOT NULL')
        for row in cursor.fetchall():
            tokens_to_save.append({
                'numero': row[0],
                'client': row[1],
                'token': row[2],
                'date': row[3],
                'source': 'heritage'
            })
        conn.close()
    except Exception as e:
        print(f'Erreur Heritage: {e}')

# Sauvegarder depuis Multi
if os.path.exists('data/soumissions_multi.db'):
    try:
        conn = sqlite3.connect('data/soumissions_multi.db')
        cursor = conn.cursor()
        cursor.execute('SELECT numero_soumission, nom_client, token, date_creation FROM soumissions WHERE token IS NOT NULL')
        for row in cursor.fetchall():
            tokens_to_save.append({
                'numero': row[0],
                'client': row[1],
                'token': row[2],
                'date': row[3],
                'source': 'multi'
            })
        conn.close()
    except Exception as e:
        print(f'Erreur Multi: {e}')

# Écrire dans un fichier persistant avec timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'{backup_dir}/tokens_backup_{timestamp}.json'
with open(backup_file, 'w') as f:
    json.dump({
        'date': datetime.now().isoformat(),
        'count': len(tokens_to_save),
        'tokens': tokens_to_save
    }, f, indent=2)

print(f'✅ {len(tokens_to_save)} tokens sauvegardés dans {backup_file}')

# Garder aussi une copie toujours accessible
with open('/opt/render/project/data/tokens_latest.json', 'w') as f:
    json.dump(tokens_to_save, f)
"

# Nettoyer les vieux backups si l'espace est limité
USAGE=$(df /opt/render/project/data | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$USAGE" -gt 80 ]; then
    echo "⚠️ Espace disque utilisé à ${USAGE}% - Nettoyage des vieux backups..."
    find /opt/render/project/data/backups -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
    find /opt/render/project/data/backups -name "tokens_backup_*.json" -mtime +30 -delete 2>/dev/null
    echo "✅ Vieux backups supprimés"
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

# NOUVEAU: Restauration des tokens après initialisation
echo ""
echo "🔄 Restauration des tokens sauvegardés..."
python3 -c "
import sqlite3
import json
import os

restored_count = 0

# Essayer de restaurer depuis le dernier backup
if os.path.exists('/opt/render/project/data/tokens_latest.json'):
    try:
        with open('/opt/render/project/data/tokens_latest.json', 'r') as f:
            tokens = json.load(f)
        
        for item in tokens:
            if item['source'] == 'heritage' and os.path.exists('data/soumissions_heritage.db'):
                try:
                    conn = sqlite3.connect('data/soumissions_heritage.db')
                    cursor = conn.cursor()
                    # Vérifier si l'enregistrement existe
                    cursor.execute('SELECT token FROM soumissions_heritage WHERE numero = ?', (item['numero'],))
                    existing = cursor.fetchone()
                    if existing and not existing[0]:
                        # Mettre à jour le token s'il est vide
                        cursor.execute('UPDATE soumissions_heritage SET token = ? WHERE numero = ?', 
                                     (item['token'], item['numero']))
                        if cursor.rowcount > 0:
                            restored_count += 1
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f'Erreur restauration Heritage: {e}')
                    
            elif item['source'] == 'multi' and os.path.exists('data/soumissions_multi.db'):
                try:
                    conn = sqlite3.connect('data/soumissions_multi.db')
                    cursor = conn.cursor()
                    # Vérifier si l'enregistrement existe
                    cursor.execute('SELECT token FROM soumissions WHERE numero_soumission = ?', (item['numero'],))
                    existing = cursor.fetchone()
                    if existing and not existing[0]:
                        # Mettre à jour le token s'il est vide
                        cursor.execute('UPDATE soumissions SET token = ? WHERE numero_soumission = ?', 
                                     (item['token'], item['numero']))
                        if cursor.rowcount > 0:
                            restored_count += 1
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f'Erreur restauration Multi: {e}')
        
        print(f'✅ {restored_count} tokens restaurés')
    except Exception as e:
        print(f'⚠️ Impossible de restaurer les tokens: {e}')
else:
    print('ℹ️ Aucun backup de tokens trouvé')
"

echo ""
echo "📊 Statistiques:"
# Compter les soumissions
if [ -f "/opt/render/project/data/soumissions_heritage.db" ]; then
    HERITAGE_COUNT=$(sqlite3 /opt/render/project/data/soumissions_heritage.db "SELECT COUNT(*) FROM soumissions_heritage" 2>/dev/null || echo "0")
    HERITAGE_TOKENS=$(sqlite3 /opt/render/project/data/soumissions_heritage.db "SELECT COUNT(*) FROM soumissions_heritage WHERE token IS NOT NULL" 2>/dev/null || echo "0")
    echo "  - Soumissions Heritage: $HERITAGE_COUNT (avec tokens: $HERITAGE_TOKENS)"
fi
if [ -f "/opt/render/project/data/soumissions_multi.db" ]; then
    MULTI_COUNT=$(sqlite3 /opt/render/project/data/soumissions_multi.db "SELECT COUNT(*) FROM soumissions" 2>/dev/null || echo "0")
    MULTI_TOKENS=$(sqlite3 /opt/render/project/data/soumissions_multi.db "SELECT COUNT(*) FROM soumissions WHERE token IS NOT NULL" 2>/dev/null || echo "0")
    echo "  - Soumissions Multi-format: $MULTI_COUNT (avec tokens: $MULTI_TOKENS)"
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