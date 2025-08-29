"""
Module de création de bons de commande personnalisables
Support multi-entreprises avec configuration dynamique basé sur l'architecture existante de C2B Construction
"""

import streamlit as st
import json
import uuid
from datetime import datetime, date
import sqlite3
import os
import base64
from pathlib import Path
import hashlib

# Import du module de configuration d'entreprise
try:
    from entreprise_config import (
        get_entreprise_config, 
        get_formatted_company_info,
        get_company_colors,
        get_company_logo,
        get_commercial_params
    )
    DYNAMIC_CONFIG = True
except ImportError:
    DYNAMIC_CONFIG = False
    # Configuration par défaut si le module n'est pas disponible
    COMPANY_INFO = {
        'name': 'Construction Héritage',
        'address': '129 Rue Poirier',
        'city': 'Saint-Jean-sur-Richelieu (Québec) J3B 4E9',
        'phone': '438-524-9193',
        'cell': '514-983-7492',
        'email': 'info@constructionheritage.ca',
        'rbq': '5788-9784-01',
        'neq': '1163835623'
    }

def get_company_info():
    """Récupère les informations de l'entreprise depuis la configuration"""
    if DYNAMIC_CONFIG:
        config = get_entreprise_config()
        return {
            'name': config.get('nom', 'Entreprise'),
            'address': config.get('adresse', ''),
            'city': f"{config.get('ville', '')} ({config.get('province', 'Québec')}) {config.get('code_postal', '')}",
            'phone': config.get('telephone_bureau', ''),
            'cell': config.get('telephone_cellulaire', ''),
            'email': config.get('email', ''),
            'rbq': config.get('rbq', ''),
            'neq': config.get('neq', '')
        }
    else:
        return COMPANY_INFO

def init_bon_commande_db():
    """Initialise la base de données pour les bons de commande"""
    db_path = 'data/bon_commande.db'
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table pour les bons de commande
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bons_commande (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_bon TEXT UNIQUE NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_bon DATE,
            fournisseur_nom TEXT,
            fournisseur_adresse TEXT,
            fournisseur_ville TEXT,
            fournisseur_code_postal TEXT,
            fournisseur_telephone TEXT,
            fournisseur_cellulaire TEXT,
            fournisseur_contact TEXT,
            client_nom TEXT,
            projet_nom TEXT,
            projet_lieu TEXT,
            ref_soumission TEXT,
            charge_projet TEXT,
            conditions_validite TEXT,
            conditions_paiement TEXT,
            date_debut DATE,
            date_fin DATE,
            signature_auteur TEXT,
            date_signature_auteur DATE,
            signature_fournisseur TEXT,
            date_signature_fournisseur DATE,
            subtotal REAL DEFAULT 0,
            tps REAL DEFAULT 0,
            tvq REAL DEFAULT 0,
            total REAL DEFAULT 0,
            statut TEXT DEFAULT 'brouillon',
            notes TEXT,
            data_json TEXT,
            derniere_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table pour les items du bon de commande
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bon_commande_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bon_commande_id INTEGER,
            numero_item INTEGER,
            titre TEXT,
            description TEXT,
            quantite REAL DEFAULT 1,
            unite TEXT DEFAULT 'unité',
            prix_unitaire REAL DEFAULT 0,
            total_item REAL DEFAULT 0,
            ordre INTEGER DEFAULT 0,
            FOREIGN KEY (bon_commande_id) REFERENCES bons_commande (id) ON DELETE CASCADE
        )
    ''')
    
    # Table pour les pièces jointes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bon_commande_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bon_commande_id INTEGER,
            nom_fichier TEXT,
            type_fichier TEXT,
            taille_fichier INTEGER,
            contenu_base64 TEXT,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bon_commande_id) REFERENCES bons_commande (id) ON DELETE CASCADE
        )
    ''')
    
    # Index pour optimiser les requêtes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_numero_bon ON bons_commande (numero_bon)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_creation ON bons_commande (date_creation)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_fournisseur ON bons_commande (fournisseur_nom)')
    
    conn.commit()
    conn.close()

def generer_numero_bon():
    """Génère automatiquement un numéro de bon de commande unique"""
    current_year = datetime.now().year
    
    db_path = 'data/bon_commande.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Chercher le dernier numéro pour l'année courante
    cursor.execute('''
        SELECT numero_bon FROM bons_commande 
        WHERE numero_bon LIKE ? 
        ORDER BY numero_bon DESC 
        LIMIT 1
    ''', (f'BC-{current_year}-%',))
    
    result = cursor.fetchone()
    
    if result:
        # Extraire le numéro de séquence
        last_number = result[0]
        try:
            sequence = int(last_number.split('-')[-1])
            new_sequence = sequence + 1
        except (ValueError, IndexError):
            new_sequence = 1
    else:
        new_sequence = 1
    
    conn.close()
    
    return f"BC-{current_year}-{new_sequence:03d}"

def sauvegarder_bon_commande(data):
    """Sauvegarde un bon de commande dans la base de données"""
    init_bon_commande_db()
    
    db_path = 'data/bon_commande.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Calculer les totaux
        subtotal = sum(item.get('total', 0) for item in data.get('items', []))
        tps = subtotal * 0.05  # 5% TPS
        tvq = subtotal * 0.09975  # 9.975% TVQ
        total = subtotal + tps + tvq
        
        # Vérifier si le bon existe déjà
        cursor.execute('SELECT id FROM bons_commande WHERE numero_bon = ?', 
                      (data.get('numeroBon'),))
        existing = cursor.fetchone()
        
        if existing:
            # Mise à jour
            cursor.execute('''
                UPDATE bons_commande SET
                    date_bon = ?, fournisseur_nom = ?, fournisseur_adresse = ?,
                    fournisseur_ville = ?, fournisseur_code_postal = ?,
                    fournisseur_telephone = ?, fournisseur_cellulaire = ?,
                    fournisseur_contact = ?, client_nom = ?, projet_nom = ?,
                    projet_lieu = ?, ref_soumission = ?, charge_projet = ?,
                    conditions_validite = ?, conditions_paiement = ?,
                    date_debut = ?, date_fin = ?, signature_auteur = ?,
                    date_signature_auteur = ?, signature_fournisseur = ?,
                    date_signature_fournisseur = ?, subtotal = ?, tps = ?,
                    tvq = ?, total = ?, data_json = ?,
                    derniere_modification = CURRENT_TIMESTAMP
                WHERE numero_bon = ?
            ''', (
                data.get('dateBon'), 
                data.get('fournisseur', {}).get('nom'),
                data.get('fournisseur', {}).get('adresse'),
                data.get('fournisseur', {}).get('ville'),
                data.get('fournisseur', {}).get('codePostal'),
                data.get('fournisseur', {}).get('tel'),
                data.get('fournisseur', {}).get('cell'),
                data.get('fournisseur', {}).get('contact'),
                data.get('projet', {}).get('nomClient'),
                data.get('projet', {}).get('nomProjet'),
                data.get('projet', {}).get('lieu'),
                data.get('projet', {}).get('refSoumission'),
                data.get('projet', {}).get('chargeProjet'),
                data.get('conditions', {}).get('validite'),
                data.get('conditions', {}).get('paiement'),
                data.get('conditions', {}).get('dateDebut'),
                data.get('conditions', {}).get('dateFin'),
                data.get('signatures', {}).get('auteur'),
                data.get('signatures', {}).get('dateAuteur'),
                data.get('signatures', {}).get('fournisseur'),
                data.get('signatures', {}).get('dateFournisseur'),
                subtotal, tps, tvq, total,
                json.dumps(data, ensure_ascii=False),
                data.get('numeroBon')
            ))
            bon_id = existing[0]
        else:
            # Insertion
            cursor.execute('''
                INSERT INTO bons_commande (
                    numero_bon, date_bon, fournisseur_nom, fournisseur_adresse,
                    fournisseur_ville, fournisseur_code_postal,
                    fournisseur_telephone, fournisseur_cellulaire,
                    fournisseur_contact, client_nom, projet_nom,
                    projet_lieu, ref_soumission, charge_projet,
                    conditions_validite, conditions_paiement,
                    date_debut, date_fin, signature_auteur,
                    date_signature_auteur, signature_fournisseur,
                    date_signature_fournisseur, subtotal, tps,
                    tvq, total, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('numeroBon'),
                data.get('dateBon'),
                data.get('fournisseur', {}).get('nom'),
                data.get('fournisseur', {}).get('adresse'),
                data.get('fournisseur', {}).get('ville'),
                data.get('fournisseur', {}).get('codePostal'),
                data.get('fournisseur', {}).get('tel'),
                data.get('fournisseur', {}).get('cell'),
                data.get('fournisseur', {}).get('contact'),
                data.get('projet', {}).get('nomClient'),
                data.get('projet', {}).get('nomProjet'),
                data.get('projet', {}).get('lieu'),
                data.get('projet', {}).get('refSoumission'),
                data.get('projet', {}).get('chargeProjet'),
                data.get('conditions', {}).get('validite'),
                data.get('conditions', {}).get('paiement'),
                data.get('conditions', {}).get('dateDebut'),
                data.get('conditions', {}).get('dateFin'),
                data.get('signatures', {}).get('auteur'),
                data.get('signatures', {}).get('dateAuteur'),
                data.get('signatures', {}).get('fournisseur'),
                data.get('signatures', {}).get('dateFournisseur'),
                subtotal, tps, tvq, total,
                json.dumps(data, ensure_ascii=False)
            ))
            bon_id = cursor.lastrowid
        
        # Supprimer les anciens items
        cursor.execute('DELETE FROM bon_commande_items WHERE bon_commande_id = ?', (bon_id,))
        
        # Insérer les nouveaux items
        for i, item in enumerate(data.get('items', [])):
            cursor.execute('''
                INSERT INTO bon_commande_items (
                    bon_commande_id, numero_item, titre, description,
                    quantite, unite, prix_unitaire, total_item, ordre
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bon_id, item.get('number'), item.get('title'),
                item.get('description'), item.get('quantity'),
                item.get('unit'), item.get('unitPrice'),
                item.get('total'), i
            ))
        
        # Gérer les pièces jointes
        if 'attachments' in data:
            cursor.execute('DELETE FROM bon_commande_attachments WHERE bon_commande_id = ?', (bon_id,))
            
            for attachment in data.get('attachments', []):
                cursor.execute('''
                    INSERT INTO bon_commande_attachments (
                        bon_commande_id, nom_fichier, type_fichier,
                        taille_fichier, contenu_base64
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    bon_id, attachment.get('name'), attachment.get('type'),
                    attachment.get('size'), attachment.get('data')
                ))
        
        conn.commit()
        return bon_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def charger_bon_commande(numero_bon):
    """Charge un bon de commande depuis la base de données"""
    db_path = 'data/bon_commande.db'
    
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Récupérer le bon de commande principal
        cursor.execute('SELECT * FROM bons_commande WHERE numero_bon = ?', (numero_bon,))
        bon = cursor.fetchone()
        
        if not bon:
            return None
        
        # Récupérer la description des colonnes
        columns = [description[0] for description in cursor.description]
        bon_dict = dict(zip(columns, bon))
        
        # Récupérer les items
        cursor.execute('''
            SELECT * FROM bon_commande_items 
            WHERE bon_commande_id = ? 
            ORDER BY ordre
        ''', (bon_dict['id'],))
        items_rows = cursor.fetchall()
        
        items_columns = [description[0] for description in cursor.description]
        items = [dict(zip(items_columns, item)) for item in items_rows]
        
        # Récupérer les pièces jointes
        cursor.execute('''
            SELECT * FROM bon_commande_attachments 
            WHERE bon_commande_id = ?
        ''', (bon_dict['id'],))
        attachments_rows = cursor.fetchall()
        
        if attachments_rows:
            attachments_columns = [description[0] for description in cursor.description]
            attachments = [dict(zip(attachments_columns, att)) for att in attachments_rows]
        else:
            attachments = []
        
        # Construire la structure de données complète
        data = {
            'numeroBon': bon_dict.get('numero_bon'),
            'dateBon': bon_dict.get('date_bon'),
            'entreprise': get_company_info(),
            'fournisseur': {
                'nom': bon_dict.get('fournisseur_nom', ''),
                'adresse': bon_dict.get('fournisseur_adresse', ''),
                'ville': bon_dict.get('fournisseur_ville', ''),
                'codePostal': bon_dict.get('fournisseur_code_postal', ''),
                'tel': bon_dict.get('fournisseur_telephone', ''),
                'cell': bon_dict.get('fournisseur_cellulaire', ''),
                'contact': bon_dict.get('fournisseur_contact', '')
            },
            'projet': {
                'nomClient': bon_dict.get('client_nom', ''),
                'nomProjet': bon_dict.get('projet_nom', ''),
                'lieu': bon_dict.get('projet_lieu', ''),
                'refSoumission': bon_dict.get('ref_soumission', ''),
                'chargeProjet': bon_dict.get('charge_projet', '')
            },
            'conditions': {
                'validite': bon_dict.get('conditions_validite', '30 jours'),
                'paiement': bon_dict.get('conditions_paiement', 'Net 30 jours'),
                'dateDebut': bon_dict.get('date_debut', ''),
                'dateFin': bon_dict.get('date_fin', '')
            },
            'signatures': {
                'auteur': bon_dict.get('signature_auteur', ''),
                'dateAuteur': bon_dict.get('date_signature_auteur', ''),
                'fournisseur': bon_dict.get('signature_fournisseur', ''),
                'dateFournisseur': bon_dict.get('date_signature_fournisseur', '')
            },
            'items': [{
                'id': item['id'],
                'number': item['numero_item'],
                'title': item['titre'] or '',
                'description': item['description'] or '',
                'quantity': item['quantite'],
                'unit': item['unite'],
                'unitPrice': item['prix_unitaire'],
                'total': item['total_item']
            } for item in items],
            'attachments': [{
                'id': att['id'],
                'name': att['nom_fichier'],
                'type': att['type_fichier'],
                'size': att['taille_fichier'],
                'data': att['contenu_base64'],
                'addedDate': att['date_ajout']
            } for att in attachments],
            'totaux': {
                'subtotal': bon_dict.get('subtotal', 0),
                'tps': bon_dict.get('tps', 0),
                'tvq': bon_dict.get('tvq', 0),
                'total': bon_dict.get('total', 0)
            }
        }
        
        return data
        
    except Exception as e:
        st.error(f"Erreur lors du chargement du bon de commande: {e}")
        return None
    finally:
        conn.close()

def lister_bons_commande():
    """Liste tous les bons de commande"""
    db_path = 'data/bon_commande.db'
    
    if not os.path.exists(db_path):
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT numero_bon, date_creation, fournisseur_nom, 
                   projet_nom, total, statut, derniere_modification
            FROM bons_commande 
            ORDER BY derniere_modification DESC
        ''')
        
        bons = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        return [dict(zip(columns, bon)) for bon in bons]
        
    except Exception as e:
        st.error(f"Erreur lors de la récupération des bons: {e}")
        return []
    finally:
        conn.close()

def supprimer_bon_commande(numero_bon):
    """Supprime un bon de commande"""
    db_path = 'data/bon_commande.db'
    
    if not os.path.exists(db_path):
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM bons_commande WHERE numero_bon = ?', (numero_bon,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {e}")
        return False
    finally:
        conn.close()

def generer_html_bon_commande(data):
    """Génère le HTML complet du bon de commande en utilisant le template existant"""
    
    company = get_company_info()
    
    # Lire le fichier HTML template
    html_template_path = Path(__file__).parent / 'bon-commande-moderne.html'
    
    try:
        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except FileNotFoundError:
        st.error("Template HTML non trouvé")
        return None
    
    # Remplacer les variables dans le HTML avec les données du bon de commande
    html_content = html_content.replace('value="Construction Héritage"', f'value="{company["name"]}"')
    html_content = html_content.replace('value="129 Rue Poirier"', f'value="{company["address"]}"')
    html_content = html_content.replace('value="Saint-Jean-sur-Richelieu (Québec) J3B 4E9"', f'value="{company["city"]}"')
    html_content = html_content.replace('value="438.524.9193"', f'value="{company["phone"]}"')
    html_content = html_content.replace('value="514.983.7492"', f'value="{company["cell"]}"')
    html_content = html_content.replace('value="info@constructionheritage.ca"', f'value="{company["email"]}"')
    html_content = html_content.replace('value="5788-9784-01"', f'value="{company["rbq"]}"')
    html_content = html_content.replace('value="1163835623"', f'value="{company["neq"]}"')
    
    # Ajouter un script pour charger les données du bon de commande
    data_script = f"""
    <script>
        // Charger les données du bon de commande
        const bonData = {json.dumps(data, ensure_ascii=False)};
        
        document.addEventListener('DOMContentLoaded', function() {{
            if (bonData && window.BOC) {{
                BOC.restoreData(bonData);
            }}
        }});
    </script>
    """
    
    # Insérer le script avant la fermeture du body
    html_content = html_content.replace('</body>', data_script + '</body>')
    
    return html_content

def exporter_bon_commande_pdf(data):
    """Exporte un bon de commande en PDF (fonction placeholder)"""
    # Cette fonction peut être étendue pour utiliser des bibliothèques comme reportlab
    # ou weasyprint pour générer des PDFs
    pass

def dupliquer_bon_commande(numero_bon_source):
    """Duplique un bon de commande existant avec un nouveau numéro"""
    data = charger_bon_commande(numero_bon_source)
    if not data:
        return None
    
    # Générer un nouveau numéro
    nouveau_numero = generer_numero_bon()
    data['numeroBon'] = nouveau_numero
    data['dateBon'] = datetime.now().strftime('%Y-%m-%d')
    
    # Réinitialiser les signatures
    data['signatures'] = {
        'auteur': '',
        'dateAuteur': '',
        'fournisseur': '',
        'dateFournisseur': ''
    }
    
    # Sauvegarder le nouveau bon
    sauvegarder_bon_commande(data)
    
    return nouveau_numero