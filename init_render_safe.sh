#!/bin/bash

# Script d'initialisation sécurisé pour Render avec disque persistant
# Ce script préserve les données existantes

echo "=========================================="
echo "Initialisation sécurisée pour Render"
echo "=========================================="

# Définir les répertoires
DATA_BASE="/data"  # Disque persistant monté par Render
DATA_DIR="${DATA_BASE}/databases"
FILES_DIR="${DATA_BASE}/files"
BACKUP_DIR="${DATA_BASE}/backups"

# Créer les répertoires s'ils n'existent pas
echo "📁 Création des répertoires..."
mkdir -p "$DATA_DIR"
mkdir -p "$FILES_DIR"
mkdir -p "$BACKUP_DIR"

# Créer des liens symboliques pour l'application
echo "🔗 Création des liens symboliques..."
if [ ! -L "data" ]; then
    # Supprimer le dossier local s'il existe
    if [ -d "data" ] && [ ! -L "data" ]; then
        rm -rf data
    fi
    ln -s "$DATA_DIR" data
fi

if [ ! -L "files" ]; then
    # Supprimer le dossier local s'il existe
    if [ -d "files" ] && [ ! -L "files" ]; then
        rm -rf files
    fi
    ln -s "$FILES_DIR" files
fi

# Fonction pour créer une sauvegarde
backup_databases() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz"
    
    echo "💾 Création d'une sauvegarde de sécurité..."
    if [ -f "${DATA_DIR}/soumissions_heritage.db" ] || [ -f "${DATA_DIR}/soumissions_multi.db" ]; then
        tar -czf "$BACKUP_FILE" -C "$DATA_DIR" . 2>/dev/null
        echo "✅ Sauvegarde créée: $BACKUP_FILE"
        
        # Garder seulement les 5 dernières sauvegardes
        ls -t ${BACKUP_DIR}/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
    else
        echo "ℹ️ Aucune base de données à sauvegarder"
    fi
}

# Fonction pour vérifier l'intégrité d'une base de données
check_database_integrity() {
    local db_path=$1
    local db_name=$2
    
    if [ -f "$db_path" ]; then
        echo "🔍 Vérification de $db_name..."
        python -c "
import sqlite3
try:
    conn = sqlite3.connect('$db_path')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\"table\"')
    table_count = cursor.fetchone()[0]
    cursor.execute('PRAGMA integrity_check')
    integrity = cursor.fetchone()[0]
    conn.close()
    
    if integrity == 'ok':
        print(f'  ✅ Base de données OK ({table_count} tables)')
    else:
        print(f'  ⚠️ Problème détecté: {integrity}')
        exit(1)
except Exception as e:
    print(f'  ❌ Erreur: {e}')
    exit(1)
"
        return $?
    else
        return 1
    fi
}

# Créer une sauvegarde avant toute modification
backup_databases

# Vérifier et initialiser les bases de données si nécessaire
echo ""
echo "📊 Vérification des bases de données..."

# Base Heritage
if check_database_integrity "${DATA_DIR}/soumissions_heritage.db" "Heritage"; then
    echo "  ✅ Base Heritage existante préservée"
else
    echo "  📝 Initialisation de la base Heritage..."
    python -c "
import sqlite3
conn = sqlite3.connect('${DATA_DIR}/soumissions_heritage.db')
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
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        lien_public TEXT
    )
''')
conn.commit()
conn.close()
print('  ✅ Base Heritage créée')
"
fi

# Base Multi-format
if check_database_integrity "${DATA_DIR}/soumissions_multi.db" "Multi-format"; then
    echo "  ✅ Base Multi-format existante préservée"
else
    echo "  📝 Initialisation de la base Multi-format..."
    python -c "
import sqlite3
conn = sqlite3.connect('${DATA_DIR}/soumissions_multi.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS soumissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_soumission TEXT UNIQUE NOT NULL,
        nom_client TEXT NOT NULL,
        email_client TEXT,
        telephone_client TEXT,
        nom_projet TEXT,
        montant_total REAL,
        file_type TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT,
        file_size INTEGER,
        file_data BLOB,
        html_preview TEXT,
        token TEXT UNIQUE NOT NULL,
        statut TEXT DEFAULT 'en_attente',
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_envoi TIMESTAMP,
        date_decision TIMESTAMP,
        commentaire_client TEXT,
        ip_client TEXT,
        lien_public TEXT,
        metadata TEXT
    )
''')
conn.commit()
conn.close()
print('  ✅ Base Multi-format créée')
"
fi

# Base Bon de commande
if check_database_integrity "${DATA_DIR}/bon_commande.db" "Bons de commande"; then
    echo "  ✅ Base Bons de commande existante préservée"
else
    echo "  ℹ️ Base Bons de commande non trouvée (sera créée à la demande)"
fi

# Base Configuration entreprise
if check_database_integrity "${DATA_DIR}/entreprise_config.db" "Configuration"; then
    echo "  ✅ Base Configuration existante préservée"
else
    echo "  ℹ️ Base Configuration non trouvée (sera créée à la demande)"
fi

# Afficher les statistiques
echo ""
echo "📈 Statistiques des données:"
if [ -f "${DATA_DIR}/soumissions_heritage.db" ]; then
    python -c "
import sqlite3
conn = sqlite3.connect('${DATA_DIR}/soumissions_heritage.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM soumissions_heritage')
count = cursor.fetchone()[0]
conn.close()
print(f'  - Soumissions Heritage: {count}')
"
fi

if [ -f "${DATA_DIR}/soumissions_multi.db" ]; then
    python -c "
import sqlite3
conn = sqlite3.connect('${DATA_DIR}/soumissions_multi.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM soumissions')
count = cursor.fetchone()[0]
conn.close()
print(f'  - Soumissions Multi-format: {count}')
"
fi

# Afficher l'espace disque
echo ""
echo "💾 Espace disque:"
df -h "$DATA_BASE" | tail -1 | awk '{print "  Utilisé: " $3 " / " $2 " (" $5 ")"}'

# Lister les fichiers
echo ""
echo "📂 Contenu du répertoire de données:"
ls -lah "$DATA_DIR" | head -10

echo ""
echo "=========================================="
echo "✅ Initialisation terminée avec succès!"
echo "🔒 Vos données sont préservées et sécurisées"
echo "=========================================="
echo ""

# Lancer l'application
echo "🚀 Démarrage de l'application..."
exec streamlit run app.py --server.port=$PORT --server.address=0.0.0.0