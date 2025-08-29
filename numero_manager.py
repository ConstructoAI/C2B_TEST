"""
Module centralisé de gestion des numéros de soumission
Garantit l'unicité des numéros entre tous les modules
"""

import sqlite3
import os
from datetime import datetime

def get_unified_next_number():
    """
    Génère le prochain numéro de soumission en consultant TOUTES les bases de données
    pour garantir l'unicité entre Heritage et Multi-format
    
    Returns:
        str: Numéro au format YYYY-XXX (ex: 2025-001)
    """
    current_year = datetime.now().year
    max_number = 0
    
    # Créer le dossier data s'il n'existe pas
    os.makedirs('data', exist_ok=True)
    
    # 1. Vérifier dans soumissions_heritage.db
    try:
        if os.path.exists('data/soumissions_heritage.db'):
            conn_heritage = sqlite3.connect('data/soumissions_heritage.db')
            cursor_heritage = conn_heritage.cursor()
            
            # Créer la table si elle n'existe pas
            cursor_heritage.execute('''
                CREATE TABLE IF NOT EXISTS soumissions_heritage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT UNIQUE,
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
            
            # Récupérer le dernier numéro de l'année courante
            cursor_heritage.execute('''
                SELECT numero FROM soumissions_heritage 
                WHERE numero LIKE ? 
                ORDER BY numero DESC 
                LIMIT 1
            ''', (f'{current_year}-%',))
            
            result = cursor_heritage.fetchone()
            if result and result[0]:
                try:
                    number = int(result[0].split('-')[1])
                    max_number = max(max_number, number)
                except (ValueError, IndexError):
                    pass
            
            conn_heritage.close()
    except Exception as e:
        print(f"Erreur lecture soumissions_heritage.db: {e}")
    
    # 2. Vérifier dans soumissions_multi.db
    try:
        if os.path.exists('data/soumissions_multi.db'):
            conn_multi = sqlite3.connect('data/soumissions_multi.db')
            cursor_multi = conn_multi.cursor()
            
            # Créer la table si elle n'existe pas
            cursor_multi.execute('''
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
            
            # Récupérer le dernier numéro de l'année courante
            cursor_multi.execute('''
                SELECT numero_soumission FROM soumissions 
                WHERE numero_soumission LIKE ? 
                ORDER BY numero_soumission DESC 
                LIMIT 1
            ''', (f'{current_year}-%',))
            
            result = cursor_multi.fetchone()
            if result and result[0]:
                try:
                    number = int(result[0].split('-')[1])
                    max_number = max(max_number, number)
                except (ValueError, IndexError):
                    pass
            
            conn_multi.close()
    except Exception as e:
        print(f"Erreur lecture soumissions_multi.db: {e}")
    
    # 3. Vérifier aussi dans bon_commande.db pour éviter tout conflit
    # (au cas où les bons de commande utilisent un format similaire)
    try:
        if os.path.exists('data/bon_commande.db'):
            conn_bon = sqlite3.connect('data/bon_commande.db')
            cursor_bon = conn_bon.cursor()
            
            # Vérifier si la table existe
            cursor_bon.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='bons_commande'
            ''')
            
            if cursor_bon.fetchone():
                # Récupérer les numéros qui pourraient ressembler à YYYY-XXX
                cursor_bon.execute('''
                    SELECT numero_bon FROM bons_commande 
                    WHERE numero_bon LIKE ? AND numero_bon NOT LIKE 'BC-%'
                    ORDER BY numero_bon DESC 
                    LIMIT 1
                ''', (f'{current_year}-%',))
                
                result = cursor_bon.fetchone()
                if result and result[0]:
                    try:
                        number = int(result[0].split('-')[1])
                        max_number = max(max_number, number)
                    except (ValueError, IndexError):
                        pass
            
            conn_bon.close()
    except Exception as e:
        # Les bons de commande peuvent ne pas exister, ce n'est pas grave
        pass
    
    # Générer le prochain numéro
    next_number = max_number + 1
    return f"{current_year}-{next_number:03d}"

def verify_number_uniqueness(numero):
    """
    Vérifie qu'un numéro n'existe pas déjà dans les bases
    
    Args:
        numero (str): Le numéro à vérifier
        
    Returns:
        bool: True si le numéro est unique, False sinon
    """
    # Vérifier dans soumissions_heritage.db
    try:
        if os.path.exists('data/soumissions_heritage.db'):
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM soumissions_heritage WHERE numero = ?', (numero,))
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                return False
    except:
        pass
    
    # Vérifier dans soumissions_multi.db
    try:
        if os.path.exists('data/soumissions_multi.db'):
            conn = sqlite3.connect('data/soumissions_multi.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM soumissions WHERE numero_soumission = ?', (numero,))
            count = cursor.fetchone()[0]
            conn.close()
            if count > 0:
                return False
    except:
        pass
    
    return True

def get_safe_unique_number():
    """
    Génère un numéro garanti unique avec vérification
    
    Returns:
        str: Numéro unique au format YYYY-XXX
    """
    max_attempts = 100  # Sécurité contre boucle infinie
    attempts = 0
    
    while attempts < max_attempts:
        numero = get_unified_next_number()
        if verify_number_uniqueness(numero):
            return numero
        attempts += 1
    
    # Si on arrive ici, il y a un problème grave
    # Générer un numéro avec timestamp pour garantir l'unicité
    timestamp = datetime.now().strftime('%H%M%S')
    return f"{datetime.now().year}-{timestamp}"

# Fonction de migration pour corriger les doublons existants
def fix_duplicate_numbers():
    """
    Corrige les numéros en double existants dans les bases
    À exécuter une fois pour nettoyer les données
    """
    current_year = datetime.now().year
    all_numbers = []
    
    # Collecter tous les numéros existants avec leur source
    try:
        if os.path.exists('data/soumissions_heritage.db'):
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, numero FROM soumissions_heritage ORDER BY created_at')
            for row in cursor.fetchall():
                all_numbers.append(('heritage', row[0], row[1]))
            conn.close()
    except:
        pass
    
    try:
        if os.path.exists('data/soumissions_multi.db'):
            conn = sqlite3.connect('data/soumissions_multi.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, numero_soumission FROM soumissions ORDER BY date_creation')
            for row in cursor.fetchall():
                all_numbers.append(('multi', row[0], row[1]))
            conn.close()
    except:
        pass
    
    # Détecter et corriger les doublons
    seen_numbers = set()
    corrections = []
    
    for source, id_val, numero in all_numbers:
        if numero in seen_numbers:
            # Doublon détecté - générer un nouveau numéro
            new_numero = get_safe_unique_number()
            corrections.append((source, id_val, numero, new_numero))
            seen_numbers.add(new_numero)
        else:
            seen_numbers.add(numero)
    
    # Appliquer les corrections
    for source, id_val, old_num, new_num in corrections:
        try:
            if source == 'heritage':
                conn = sqlite3.connect('data/soumissions_heritage.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE soumissions_heritage SET numero = ? WHERE id = ?', (new_num, id_val))
                conn.commit()
                conn.close()
                print(f"Heritage: Corrigé {old_num} -> {new_num}")
            elif source == 'multi':
                conn = sqlite3.connect('data/soumissions_multi.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE soumissions SET numero_soumission = ? WHERE id = ?', (new_num, id_val))
                conn.commit()
                conn.close()
                print(f"Multi: Corrigé {old_num} -> {new_num}")
        except Exception as e:
            print(f"Erreur correction {old_num}: {e}")
    
    return len(corrections)

if __name__ == "__main__":
    # Test du module
    print("Test du gestionnaire de numéros unifié")
    print("-" * 40)
    
    # Tester la génération
    numero = get_safe_unique_number()
    print(f"Prochain numéro disponible: {numero}")
    
    # Vérifier l'unicité
    is_unique = verify_number_uniqueness(numero)
    print(f"Le numéro {numero} est unique: {is_unique}")
    
    # Proposer la correction des doublons
    print("\nVérification des doublons...")
    corrections = fix_duplicate_numbers()
    if corrections > 0:
        print(f"✅ {corrections} doublons corrigés")
    else:
        print("✅ Aucun doublon détecté")