import streamlit as st
import sqlite3
import hashlib
import uuid
import base64
import os
from datetime import datetime
from pathlib import Path
import mimetypes
import json
import shutil
from io import BytesIO
import re

# Import du module de bons de commande
try:
    from bon_commande import (
        init_bon_commande_db,
        generer_numero_bon,
        sauvegarder_bon_commande,
        charger_bon_commande,
        lister_bons_commande,
        supprimer_bon_commande,
        generer_html_bon_commande,
        dupliquer_bon_commande
    )
    BON_COMMANDE_AVAILABLE = True
except ImportError:
    BON_COMMANDE_AVAILABLE = False
    print("Module bon_commande non disponible")

# Import du module de compatibilité
try:
    from streamlit_compat import rerun, clear_cache, show_html, get_query_params, set_query_params
except ImportError:
    # Fallback si le module n'est pas disponible
    def rerun():
        if hasattr(st, 'rerun'):
            st.rerun()
        elif hasattr(st, 'experimental_rerun'):
            st.experimental_rerun()
    
    def clear_cache():
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
    
    def show_html(html_content, height=2000, scrolling=True):
        st.components.v1.html(html_content, height=height, scrolling=scrolling)
    
    def get_query_params():
        if hasattr(st, 'experimental_get_query_params'):
            return st.experimental_get_query_params()
        return {}
    
    def set_query_params(**params):
        if hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params(**params)

# Configuration
st.set_page_config(
    page_title="C2B Construction - Portail Multi-Format",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de la base de données
if os.getenv('RENDER'):
    DATA_DIR = '/opt/render/project/data'
    FILES_DIR = '/opt/render/project/files'
else:
    DATA_DIR = os.getenv('DATA_DIR', os.path.join(os.getcwd(), 'data'))
    FILES_DIR = os.getenv('FILES_DIR', os.path.join(os.getcwd(), 'files'))
    
# Créer les dossiers si nécessaire
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(DATA_DIR, 'soumissions_multi.db')

# Mot de passe admin
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin2025')

# Types de fichiers supportés
SUPPORTED_EXTENSIONS = {
    'Documents': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
    'Web': ['.html', '.htm'],
    'Texte': ['.txt', '.csv', '.rtf']
}

# Flatten pour obtenir toutes les extensions
ALL_EXTENSIONS = [ext for exts in SUPPORTED_EXTENSIONS.values() for ext in exts]

def init_database():
    """Initialise la base de données avec support multi-format"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Table améliorée pour support multi-format
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS soumissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_soumission TEXT UNIQUE NOT NULL,
            nom_client TEXT NOT NULL,
            email_client TEXT,
            telephone_client TEXT,
            nom_projet TEXT,
            montant_total REAL,
            
            -- Nouvelles colonnes pour multi-format
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
            
            -- Métadonnées additionnelles
            metadata TEXT
        )
    ''')
    
    # Index pour améliorer les performances
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_token ON soumissions(token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_statut ON soumissions(statut)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_numero ON soumissions(numero_soumission)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON soumissions(file_type)')
    
    conn.commit()
    conn.close()

def get_file_type(file):
    """Détermine le type de fichier"""
    if file.name:
        ext = Path(file.name).suffix.lower()
        mime_type = mimetypes.guess_type(file.name)[0]
        
        return {
            'extension': ext,
            'mime_type': mime_type,
            'category': get_file_category(ext),
            'name': file.name
        }
    return None

def get_file_category(extension):
    """Retourne la catégorie du fichier"""
    for category, extensions in SUPPORTED_EXTENSIONS.items():
        if extension in extensions:
            return category
    return 'Autre'

def save_file_to_disk(file, submission_id):
    """Sauvegarde le fichier sur disque"""
    file_info = get_file_type(file)
    if not file_info:
        return None
    
    # Créer un nom unique pour éviter les conflits
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = f"{submission_id}_{timestamp}_{file_info['name']}"
    file_path = os.path.join(FILES_DIR, safe_name)
    
    # Sauvegarder le fichier
    with open(file_path, 'wb') as f:
        f.write(file.getbuffer())
    
    return file_path

def extract_info_from_pdf(file):
    """Extrait les informations d'un PDF"""
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages[:3]:  # Lire seulement les 3 premières pages
            text += page.extract_text()
        
        # Extraction basique
        nom_client = "Client"
        nom_projet = "Projet"
        montant = 0.0
        
        # Chercher des patterns dans le texte
        # Pattern client
        client_patterns = [
            r'Client\s*:\s*([^\n]+)',
            r'Pour\s*:\s*([^\n]+)',
            r'Destinataire\s*:\s*([^\n]+)',
            r'Nom\s*:\s*([^\n]+)'
        ]
        for pattern in client_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nom_client = match.group(1).strip()
                break
        
        # Pattern projet
        projet_patterns = [
            r'Projet\s*:\s*([^\n]+)',
            r'Objet\s*:\s*([^\n]+)',
            r'Référence\s*:\s*([^\n]+)'
        ]
        for pattern in projet_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nom_projet = match.group(1).strip()
                break
        
        # Pattern montant
        montant_patterns = [
            r'Total.*?([0-9\s]+[,.]?\d*)\s*\$',
            r'Montant.*?([0-9\s]+[,.]?\d*)\s*\$',
            r'\$\s*([0-9\s]+[,.]?\d*)',
            r'([0-9]{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*\$'
        ]
        
        montants = []
        for pattern in montant_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    # Nettoyer et convertir
                    cleaned = re.sub(r'[^\d,.]', '', match)
                    cleaned = cleaned.replace(',', '.')
                    value = float(cleaned)
                    if value > 100:  # Ignorer les petits montants
                        montants.append(value)
                except:
                    continue
        
        if montants:
            montant = max(montants)  # Prendre le montant le plus élevé
        
        return nom_client, nom_projet, montant
        
    except ImportError:
        st.warning("PyPDF2 n'est pas installé. Extraction PDF basique.")
        return "Client", "Projet", 0.0
    except Exception as e:
        st.error(f"Erreur extraction PDF: {e}")
        return "Client", "Projet", 0.0

def extract_info_from_file(file, file_type):
    """Extrait les informations selon le type de fichier"""
    if file_type['extension'] == '.pdf':
        return extract_info_from_pdf(file)
    elif file_type['extension'] in ['.html', '.htm']:
        # Utiliser l'ancienne méthode pour HTML
        html_content = file.read().decode('utf-8')
        return extract_info_from_html(html_content)
    else:
        # Pour les autres formats, demander saisie manuelle
        return "Client", "Projet", 0.0

def extract_info_from_html(html_content):
    """Extrait les informations du HTML (reprise de l'ancienne méthode)"""
    numero = get_next_submission_number()
    
    # Extraction simplifiée
    nom_client = "Client"
    nom_projet = "Projet" 
    montant = 0.0
    
    # Patterns pour extraction
    if 'nomClient' in html_content:
        match = re.search(r'id=["\']?nomClient["\']?[^>]*>([^<]+)<', html_content)
        if match:
            nom_client = match.group(1).strip()
    
    if 'nomProjet' in html_content:
        match = re.search(r'id=["\']?nomProjet["\']?[^>]*>([^<]+)<', html_content)
        if match:
            nom_projet = match.group(1).strip()
    
    # Extraction montant
    if 'grandTotal' in html_content:
        match = re.search(r'id=["\']?grandTotal["\']?[^>]*>([^<]+)<', html_content)
        if match:
            try:
                cleaned = re.sub(r'[^\d,.]', '', match.group(1))
                montant = float(cleaned.replace(',', '.'))
            except:
                pass
    
    return nom_client, nom_projet, montant

def get_next_submission_number():
    """Génère le prochain numéro de soumission en utilisant le gestionnaire unifié"""
    try:
        from numero_manager import get_safe_unique_number
        return get_safe_unique_number()
    except ImportError:
        # Fallback sur l'ancienne méthode si le module n'est pas disponible
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        current_year = datetime.now().year
        
        cursor.execute('''
            SELECT numero_soumission 
            FROM soumissions 
            WHERE numero_soumission LIKE ? 
            ORDER BY id DESC 
            LIMIT 1
        ''', (f'{current_year}-%',))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            try:
                last_number = int(result[0].split('-')[1])
                next_number = last_number + 1
            except:
                next_number = 1
        else:
            next_number = 1
        
        return f"{current_year}-{next_number:03d}"

def generate_token():
    """Génère un token unique"""
    return str(uuid.uuid4())

def get_base_url():
    """Retourne l'URL de base"""
    # D'abord vérifier si une URL personnalisée est définie
    if os.getenv('APP_URL'):
        return os.getenv('APP_URL')
    # Sinon, vérifier si on est sur Render
    elif os.getenv('RENDER'):
        # URL de production sur Render - à ajuster selon votre URL réelle
        return 'https://c2b-heritage.onrender.com'
    else:
        # URL locale pour développement
        return 'http://localhost:8501'

def save_submission_multi(numero, nom_client, email_client, tel_client, nom_projet, montant, file, file_type):
    """Sauvegarde une soumission multi-format"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    token = generate_token()
    lien = f"{get_base_url()}/?token={token}"
    
    # Sauvegarder le fichier
    temp_id = str(uuid.uuid4())
    file_path = save_file_to_disk(file, temp_id)
    file_size = file.size
    
    # Pour HTML, on stocke aussi le contenu pour compatibilité
    html_preview = None
    if file_type['extension'] in ['.html', '.htm']:
        file.seek(0)
        html_preview = file.read().decode('utf-8')
    
    # Metadata JSON
    metadata = json.dumps({
        'original_name': file_type['name'],
        'mime_type': file_type['mime_type'],
        'upload_time': datetime.now().isoformat(),
        'category': file_type['category']
    })
    
    date_creation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO soumissions 
        (numero_soumission, nom_client, email_client, telephone_client, 
         nom_projet, montant_total, file_type, file_name, file_path, 
         file_size, html_preview, token, lien_public, date_creation, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (numero, nom_client, email_client, tel_client, nom_projet, 
          montant, file_type['extension'], file_type['name'], file_path,
          file_size, html_preview, token, lien, date_creation, metadata))
    
    conn.commit()
    submission_id = cursor.lastrowid
    conn.close()
    
    return submission_id, token, lien

def get_submission_by_token(token):
    """Récupère une soumission par son token (Multi-format ET Heritage)"""
    # Chercher d'abord dans Multi-format
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM soumissions WHERE token = ?', (token,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        columns = ['id', 'numero_soumission', 'nom_client', 'email_client', 
                  'telephone_client', 'nom_projet', 'montant_total', 
                  'file_type', 'file_name', 'file_path', 'file_size', 
                  'file_data', 'html_preview', 'token', 'statut', 
                  'date_creation', 'date_envoi', 'date_decision',
                  'commentaire_client', 'ip_client', 'lien_public', 'metadata']
        return dict(zip(columns, row))
    
    # Si pas trouvé, chercher dans Heritage
    try:
        conn_heritage = sqlite3.connect('data/soumissions_heritage.db')
        cursor_heritage = conn_heritage.cursor()
        
        cursor_heritage.execute('''
            SELECT id, numero, client_nom, projet_nom, montant_total, 
                   statut, token, data, created_at, lien_public
            FROM soumissions_heritage 
            WHERE token = ?
        ''', (token,))
        
        row_heritage = cursor_heritage.fetchone()
        conn_heritage.close()
        
        if row_heritage:
            # Convertir en format compatible avec Multi-format
            import json
            data = json.loads(row_heritage[7]) if row_heritage[7] else {}
            
            return {
                'id': row_heritage[0],
                'numero_soumission': row_heritage[1],
                'nom_client': row_heritage[2],
                'email_client': data.get('client', {}).get('courriel', ''),
                'telephone_client': data.get('client', {}).get('telephone', ''),
                'nom_projet': row_heritage[3],
                'montant_total': row_heritage[4],
                'file_type': 'heritage',
                'file_name': f'Soumission_{row_heritage[1]}.html',
                'file_path': None,
                'file_size': 0,
                'file_data': None,
                'html_preview': None,
                'token': row_heritage[6],
                'statut': row_heritage[5],
                'date_creation': row_heritage[8],
                'date_envoi': None,
                'date_decision': None,
                'commentaire_client': None,
                'ip_client': None,
                'lien_public': row_heritage[9],
                'metadata': row_heritage[7],
                'is_heritage': True  # Marqueur pour identifier Heritage
            }
    except Exception as e:
        print(f"Erreur recherche Heritage: {e}")
    
    return None

def update_submission_status(token, statut, commentaire=None):
    """Met à jour le statut d'une soumission (Multi-format ET Heritage)"""
    date_decision = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated = False
    
    # Essayer d'abord dans Multi-format
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE soumissions 
        SET statut = ?, date_decision = ?, commentaire_client = ?
        WHERE token = ?
    ''', (statut, date_decision, commentaire, token))
    
    if cursor.rowcount > 0:
        updated = True
    
    conn.commit()
    conn.close()
    
    # Si pas trouvé dans Multi-format, essayer Heritage
    if not updated:
        try:
            conn_heritage = sqlite3.connect('data/soumissions_heritage.db')
            cursor_heritage = conn_heritage.cursor()
            
            # Heritage n'a pas les mêmes colonnes, adapter
            cursor_heritage.execute('''
                UPDATE soumissions_heritage 
                SET statut = ?, updated_at = ?
                WHERE token = ?
            ''', (statut, date_decision, token))
            
            conn_heritage.commit()
            conn_heritage.close()
        except Exception as e:
            print(f"Erreur mise à jour Heritage: {e}")

def get_all_submissions():
    """Récupère toutes les soumissions des deux tables"""
    submissions = []
    
    # Récupérer les soumissions de la table principale
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, numero_soumission, nom_client, nom_projet, montant_total,
               statut, date_creation, date_decision, lien_public,
               email_client, telephone_client, file_type, file_name
        FROM soumissions
        ORDER BY date_creation DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        submissions.append({
            'id': row[0],
            'numero': row[1],
            'client': row[2],
            'projet': row[3],
            'montant': row[4],
            'statut': row[5],
            'date_creation': row[6],
            'date_decision': row[7],
            'lien': row[8],
            'email': row[9],
            'telephone': row[10],
            'file_type': row[11],
            'file_name': row[12],
            'source': 'uploaded'  # Marquer comme document uploadé
        })
    
    # Récupérer les soumissions Heritage
    try:
        conn_heritage = sqlite3.connect('data/soumissions_heritage.db')
        cursor_heritage = conn_heritage.cursor()
        
        # D'abord vérifier les colonnes disponibles
        cursor_heritage.execute("PRAGMA table_info(soumissions_heritage)")
        columns = [column[1] for column in cursor_heritage.fetchall()]
        
        # Construire la requête en fonction des colonnes disponibles
        if 'lien_public' in columns:
            cursor_heritage.execute('''
                SELECT id, numero, client_nom, projet_nom, montant_total,
                       statut, created_at, updated_at, lien_public
                FROM soumissions_heritage
                ORDER BY created_at DESC
            ''')
            
            heritage_rows = cursor_heritage.fetchall()
            conn_heritage.close()
            
            for row in heritage_rows:
                submissions.append({
                    'id': f"H{row[0]}",  # Préfixe H pour distinguer
                    'numero': row[1],
                    'client': row[2],
                    'projet': row[3],
                    'montant': row[4],
                    'statut': row[5],
                    'date_creation': row[6],
                    'date_decision': row[7] if row[5] != 'en_attente' else None,
                    'lien': row[8] if row[8] else f"{get_base_url()}/soumission_heritage?id={row[0]}",
                    'email': None,  # Pas stocké dans Heritage pour l'instant
                    'telephone': None,  # Pas stocké dans Heritage pour l'instant
                    'file_type': '.html',  # Type par défaut pour Heritage
                    'file_name': f"Soumission_{row[1]}.html",
                    'source': 'heritage'  # Marquer comme soumission Heritage
                })
        else:
            # Ancien format sans lien_public
            cursor_heritage.execute('''
                SELECT id, numero, client_nom, projet_nom, montant_total,
                       statut, created_at, updated_at
                FROM soumissions_heritage
                ORDER BY created_at DESC
            ''')
            
            heritage_rows = cursor_heritage.fetchall()
            conn_heritage.close()
            
            for row in heritage_rows:
                submissions.append({
                    'id': f"H{row[0]}",  # Préfixe H pour distinguer
                    'numero': row[1],
                    'client': row[2],
                    'projet': row[3],
                    'montant': row[4],
                    'statut': row[5],
                    'date_creation': row[6],
                    'date_decision': row[7] if row[5] != 'en_attente' else None,
                    'lien': f"{get_base_url()}/soumission_heritage?id={row[0]}",
                    'email': None,
                    'telephone': None,
                    'file_type': '.html',
                    'file_name': f"Soumission_{row[1]}.html",
                    'source': 'heritage'
                })
    except Exception as e:
        print(f"Erreur récupération soumissions Heritage: {e}")
    
    # Trier par date de création décroissante
    submissions.sort(key=lambda x: x['date_creation'] if x['date_creation'] else '', reverse=True)
    
    return submissions

def create_approval_page(submission):
    """Crée une page d'approbation pour tous les types de fichiers"""
    token = submission['token']
    
    # CSS pour la page d'approbation
    approval_css = """
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            color: #2d3748;
            margin: 0 0 10px 0;
            font-size: 32px;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .info-item {
            display: flex;
            align-items: center;
            padding: 10px;
            background: #f7fafc;
            border-radius: 8px;
        }
        
        .info-label {
            font-weight: 600;
            color: #4a5568;
            margin-right: 10px;
        }
        
        .info-value {
            color: #2d3748;
        }
        
        .document-viewer {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            min-height: calc(100vh - 300px);
            display: flex;
            flex-direction: column;
        }
        
        #document-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            min-height: calc(100vh - 400px);
        }
        
        #document-content iframe {
            flex: 1;
            width: 100%;
        }
        
        .viewer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 15px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 20px;
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-icon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 8px;
            font-size: 20px;
        }
        
        .approval-section {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .approval-title {
            font-size: 28px;
            color: #2d3748;
            margin-bottom: 15px;
            font-weight: 700;
        }
        
        .approval-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 30px;
        }
        
        .approval-btn {
            padding: 18px 45px;
            font-size: 17px;
            font-weight: 700;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            min-width: 200px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.3s ease;
        }
        
        .approve-btn {
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
        }
        
        .approve-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(72, 187, 120, 0.3);
        }
        
        .reject-btn {
            background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
            color: white;
        }
        
        .reject-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(245, 101, 101, 0.3);
        }
        
        .download-btn {
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
            color: white;
            padding: 12px 25px;
            border-radius: 8px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s ease;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(66, 153, 225, 0.3);
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 14px;
        }
        
        .status-en-attente {
            background: #fef5e7;
            color: #f39c12;
        }
        
        .status-approuvee {
            background: #d5f4e6;
            color: #27ae60;
        }
        
        .status-refusee {
            background: #fadbd8;
            color: #e74c3c;
        }
        
        iframe {
            width: 100%;
            height: 800px;
            border: none;
            border-radius: 10px;
        }
        
        .no-preview {
            text-align: center;
            padding: 60px;
            color: #718096;
        }
        
        .no-preview i {
            font-size: 64px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        @media (max-width: 768px) {
            .approval-buttons {
                flex-direction: column;
            }
            
            .approval-btn {
                width: 100%;
            }
        }
        
        /* Styles pour l'impression */
        @media print {
            /* Cacher les éléments non nécessaires */
            .approval-section, 
            .download-btn,
            button {
                display: none !important;
            }
            
            /* Forcer les couleurs et fonds */
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
            
            /* Configuration de la page */
            @page {
                size: A4;
                margin: 1cm;
            }
            
            /* Éviter les coupures de page */
            .info-section, 
            .document-viewer {
                page-break-inside: avoid;
            }
            
            /* Réduire les marges et paddings */
            .container {
                max-width: 100% !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            /* Afficher l'iframe en entier */
            iframe {
                height: auto !important;
                max-height: none !important;
                page-break-inside: auto;
            }
            
            /* Forcer l'affichage du contenu complet */
            #document-content {
                height: auto !important;
                overflow: visible !important;
            }
            
            /* Conserver les couleurs de fond */
            .header {
                background: #3b82f6 !important;
                color: white !important;
            }
            
            .info-grid {
                background: #f1f5f9 !important;
            }
        }
    </style>
    """
    
    # Gérer les soumissions Heritage différemment
    is_heritage = submission.get('is_heritage', False) or submission.get('file_type') == 'heritage'
    
    if is_heritage:
        file_icon = '🏗️'
        file_name = f"Soumission Heritage #{submission['numero_soumission']}"
        file_type = "Heritage"
        file_size_kb = 0  # Pas de taille pour Heritage
    else:
        # Déterminer l'icône selon le type de fichier
        file_icons = {
            '.pdf': '📄',
            '.doc': '📝', '.docx': '📝',
            '.xls': '📊', '.xlsx': '📊',
            '.ppt': '📑', '.pptx': '📑',
            '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️',
            '.html': '🌐', '.htm': '🌐'
        }
        file_icon = file_icons.get(submission.get('file_type', ''), '📎')
        file_name = submission.get('file_name', 'Document')
        file_type = submission.get('file_type', 'Inconnu')
        file_size_kb = submission.get('file_size', 0) / 1024 if submission.get('file_size') else 0
    
    # Créer le HTML de la page
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Soumission {submission['numero_soumission']} - Approbation</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        {approval_css}
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏗️ Soumission #{submission['numero_soumission']}</h1>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Client:</span>
                        <span class="info-value">{submission['nom_client']}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Projet:</span>
                        <span class="info-value">{submission['nom_projet'] or 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Montant:</span>
                        <span class="info-value">${submission['montant_total']:,.2f}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Statut:</span>
                        <span class="status-badge status-{submission['statut']}">{submission['statut'].replace('_', ' ').title()}</span>
                    </div>
                </div>
            </div>
            
            <div class="document-viewer">
                <div class="viewer-header">
                    <div class="file-info">
                        <div class="file-icon">{file_icon}</div>
                        <div>
                            <div style="font-weight: 600; color: #2d3748;">{file_name}</div>
                            <div style="color: #718096; font-size: 14px;">
                                Type: {file_type} {"" if is_heritage else f"| Taille: {file_size_kb:.1f} KB"}
                            </div>
                        </div>
                    </div>
                    {"" if is_heritage else f'<a href="data:application/octet-stream;base64,{get_file_download_data(submission)}" download="{file_name}" class="download-btn"><i class="fas fa-download"></i> Télécharger</a>'}
                </div>
                
                <div id="document-content">
                    {get_document_preview(submission)}
                </div>
            </div>
    """
    
    # Ajouter les boutons d'approbation et de téléchargement PDF si en attente
    if submission['statut'] == 'en_attente':
        html += f"""
            <div class="approval-section">
                <div class="approval-title">📋 Décision sur cette soumission</div>
                <p style="color: #718096;">Veuillez examiner le document ci-dessus et indiquer votre décision</p>
                <div class="approval-buttons">
                    <a href="?token={token}&action=approve" class="approval-btn approve-btn">
                        <i class="fas fa-check"></i> APPROUVER
                    </a>
                    <a href="?token={token}&action=reject" class="approval-btn reject-btn">
                        <i class="fas fa-times"></i> REFUSER
                    </a>
                    <button onclick="window.print()" class="approval-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <i class="fas fa-print"></i> IMPRIMER PDF
                    </button>
                </div>
            </div>
        """
    elif submission['statut'] == 'approuvee':
        html += f"""
            <div class="approval-section" style="background: #d5f4e6;">
                <div class="approval-title" style="color: #27ae60;">
                    <i class="fas fa-check-circle"></i> Soumission Approuvée
                </div>
                <p style="color: #27ae60;">Cette soumission a été approuvée avec succès.</p>
                <div class="approval-buttons" style="margin-top: 20px;">
                    <button onclick="window.print()" class="approval-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <i class="fas fa-print"></i> IMPRIMER PDF
                    </button>
                </div>
            </div>
        """
    else:
        html += f"""
            <div class="approval-section" style="background: #fadbd8;">
                <div class="approval-title" style="color: #e74c3c;">
                    <i class="fas fa-times-circle"></i> Soumission Refusée
                </div>
                <p style="color: #e74c3c;">Cette soumission a été refusée.</p>
                <div class="approval-buttons" style="margin-top: 20px;">
                    <button onclick="window.print()" class="approval-btn" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <i class="fas fa-print"></i> IMPRIMER PDF
                    </button>
                </div>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

def get_file_download_data(submission):
    """Encode le fichier en base64 pour le téléchargement"""
    import base64
    
    # Essayer d'abord file_data (BLOB dans la base)
    if submission.get('file_data'):
        try:
            # Si file_data est déjà en bytes
            if isinstance(submission['file_data'], bytes):
                return base64.b64encode(submission['file_data']).decode()
            # Si c'est déjà en base64 string
            elif isinstance(submission['file_data'], str):
                return submission['file_data']
        except:
            pass
    
    # Sinon essayer file_path
    file_path = submission.get('file_path', '')
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            return base64.b64encode(file_data).decode()
        except:
            pass
    
    return ""

def get_document_preview(submission):
    """Génère l'aperçu du document selon son type"""
    # Gérer les soumissions Heritage
    is_heritage = submission.get('is_heritage', False) or submission.get('file_type') == 'heritage'
    
    if is_heritage:
        # Pour Heritage, générer le HTML depuis les données
        try:
            import json
            from soumission_heritage import generate_html_for_pdf
            
            # Récupérer les données depuis metadata
            data_json = submission.get('metadata', '{}')
            if data_json:
                soumission_data = json.loads(data_json)
                
                # Reconstruire session_state temporairement
                import streamlit as st
                old_data = st.session_state.get('soumission_data', None)
                st.session_state.soumission_data = soumission_data
                
                # Générer le HTML
                html_content = generate_html_for_pdf()
                
                # Restaurer l'ancien état
                if old_data:
                    st.session_state.soumission_data = old_data
                elif 'soumission_data' in st.session_state:
                    del st.session_state.soumission_data
                
                # Encoder en base64 pour l'iframe
                import base64
                html_b64 = base64.b64encode(html_content.encode()).decode()
                return f'<iframe src="data:text/html;base64,{html_b64}" style="width: 100%; height: 1000px; border: none;"></iframe>'
            else:
                return '<div class="no-preview"><h3>Données Heritage non disponibles</h3></div>'
        except Exception as e:
            return f'<div class="no-preview"><h3>Erreur Heritage: {str(e)}</h3></div>'
    
    # Code original pour les autres types
    file_type = submission.get('file_type', '')
    token = submission['token']
    
    # Vérifier d'abord si on a file_data (BLOB)
    has_file_data = submission.get('file_data') and len(submission.get('file_data', b'')) > 0
    
    # Récupérer le chemin du fichier
    file_path = submission.get('file_path', '')
    has_file_path = file_path and os.path.exists(file_path)
    
    # Si ni file_data ni file_path valide, afficher erreur
    if not has_file_data and not has_file_path:
        # Essayer de récupérer depuis la base de données
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT file_data FROM soumissions WHERE token = ?', (token,))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                submission['file_data'] = result[0]
                has_file_data = True
        except:
            pass
        
        if not has_file_data:
            return f"""
                <div class="no-preview">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Fichier non trouvé</h3>
                    <p>Le fichier n'a pas pu être trouvé sur le serveur.</p>
                    <p style="font-size: 12px; color: #666;">
                        Chemin testé: {file_path or 'Aucun'}<br>
                        Données BLOB: {'Oui' if has_file_data else 'Non'}
                    </p>
                </div>
            """
    
    if file_type in ['.pdf']:
        # Utiliser le module pdf_viewer pour générer l'aperçu PDF
        from pdf_viewer import create_pdf_viewer_html
        try:
            # Générer le HTML complet pour le viewer PDF
            pdf_html = create_pdf_viewer_html(file_path, token, show_buttons=False)
            # Encoder en base64 pour l'iframe
            import base64
            html_b64 = base64.b64encode(pdf_html.encode()).decode()
            return f"""
                <iframe src="data:text/html;base64,{html_b64}" style="width: 100%; height: 1000px; border: none;"></iframe>
            """
        except Exception as e:
            return f"""
                <div class="no-preview">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erreur lors du chargement du PDF</h3>
                    <p>Impossible d'afficher le PDF : {str(e)}</p>
                </div>
            """
    elif file_type in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
        # Afficher directement les images en base64
        try:
            import base64
            
            # Essayer d'abord file_data (BLOB)
            if has_file_data:
                img_data = submission['file_data']
                if isinstance(img_data, str):
                    # Si c'est déjà en base64
                    img_b64 = img_data
                else:
                    # Si c'est en bytes
                    img_b64 = base64.b64encode(img_data).decode()
            elif has_file_path:
                # Sinon lire depuis le fichier
                with open(file_path, 'rb') as f:
                    img_data = f.read()
                img_b64 = base64.b64encode(img_data).decode()
            else:
                raise Exception("Aucune source de données")
            
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.svg': 'image/svg+xml'
            }
            mime_type = mime_types.get(file_type, 'image/jpeg')
            return f"""
                <div style="text-align: center; padding: 20px;">
                    <img src="data:{mime_type};base64,{img_b64}" style="max-width: 100%; height: auto; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                </div>
            """
        except Exception as e:
            return f"""
                <div class="no-preview">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erreur lors du chargement de l'image</h3>
                    <p>Impossible d'afficher l'image : {str(e)}</p>
                </div>
            """
    elif file_type in ['.html', '.htm']:
        # Afficher le HTML dans une iframe
        if submission.get('html_preview'):
            # Encoder en base64 pour éviter les problèmes
            import base64
            html_b64 = base64.b64encode(submission['html_preview'].encode()).decode()
            return f"""
                <iframe src="data:text/html;base64,{html_b64}" style="width: 100%; height: 800px; border: none;"></iframe>
            """
        else:
            # Lire le fichier HTML depuis le disque
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                import base64
                html_b64 = base64.b64encode(html_content.encode()).decode()
                return f"""
                    <iframe src="data:text/html;base64,{html_b64}" style="width: 100%; height: 800px; border: none;"></iframe>
                """
            except Exception as e:
                return f"""
                    <div class="no-preview">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Erreur lors du chargement du HTML</h3>
                        <p>Impossible d'afficher le HTML : {str(e)}</p>
                    </div>
                """
    else:
        # Pas d'aperçu disponible - Proposer le téléchargement direct du fichier
        import base64
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            file_b64 = base64.b64encode(file_data).decode()
            
            # Déterminer le type MIME
            mime_types = {
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }
            mime_type = mime_types.get(file_type, 'application/octet-stream')
            
            return f"""
                <div class="no-preview">
                    <i class="fas fa-file"></i>
                    <h3>Aperçu non disponible</h3>
                    <p>Le format {file_type} ne peut pas être affiché directement.</p>
                    <p>Veuillez télécharger le fichier pour le consulter.</p>
                    <a href="data:{mime_type};base64,{file_b64}" download="{submission['file_name']}" class="download-btn" style="margin-top: 20px;">
                        <i class="fas fa-download"></i> Télécharger le document
                    </a>
                </div>
            """
        except Exception as e:
            return f"""
                <div class="no-preview">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Erreur</h3>
                    <p>Impossible de préparer le fichier : {str(e)}</p>
                </div>
            """


def show_heritage_client_view(token):
    """Affiche la vue client pour une soumission Heritage"""
    try:
        import sqlite3
        import soumission_heritage
        import base64
        
        # Récupérer la soumission avec le token
        conn = sqlite3.connect('data/soumissions_heritage.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, numero, client_nom, projet_nom, montant_total, statut, data
            FROM soumissions_heritage 
            WHERE token = ?
        ''', (token,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            st.title(f"📄 Soumission {result[1]}")
            st.caption(f"Client: {result[2]} | Projet: {result[3]}")
            
            # Afficher le statut
            status_icons = {
                'en_attente': ('⏳', 'En attente', 'warning'),
                'approuvee': ('✅', 'Approuvée', 'success'),
                'refusee': ('❌', 'Refusée', 'error')
            }
            
            icon, label, type_msg = status_icons.get(result[5], ('❓', 'Inconnu', 'info'))
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if result[5] == 'en_attente':
                    st.info(f"{icon} **Statut:** {label} - En attente de votre décision")
                elif result[5] == 'approuvee':
                    st.success(f"{icon} **Statut:** {label}")
                elif result[5] == 'refusee':
                    st.error(f"{icon} **Statut:** {label}")
            
            # Générer et afficher le HTML
            import json
            data = json.loads(result[6])
            
            # S'assurer que soumission_data existe dans session_state
            if 'soumission_data' not in st.session_state:
                st.session_state.soumission_data = {}
            
            # Restaurer les données dans session_state
            st.session_state.soumission_data = data
            for key, value in data.items():
                st.session_state[key] = value
            
            # Générer le HTML
            html_content = soumission_heritage.generate_html()
            
            # Ajouter le bouton de téléchargement HTML pour impression
            with col2:
                # Préparer le HTML pour l'impression avec styles optimisés
                html_for_print = html_content.replace('</head>', '''
                <style>
                @media print {
                    body { 
                        margin: 0; 
                        padding: 10mm;
                        font-size: 12pt;
                    }
                    .page-break { 
                        page-break-after: always; 
                    }
                    * {
                        -webkit-print-color-adjust: exact !important;
                        print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }
                    @page {
                        size: A4;
                        margin: 15mm;
                    }
                    /* Cacher les éléments non nécessaires */
                    button, .no-print {
                        display: none !important;
                    }
                }
                /* Message pour guider l'utilisateur */
                .print-instructions {
                    display: none;
                    padding: 20px;
                    background: #f0f8ff;
                    border: 2px solid #4a90e2;
                    border-radius: 8px;
                    margin: 20px 0;
                }
                @media screen {
                    .print-instructions {
                        display: block;
                    }
                }
                </style>
                <script>
                window.onload = function() {
                    // Ajouter les instructions
                    var instructions = document.createElement('div');
                    instructions.className = 'print-instructions';
                    instructions.innerHTML = '<h3>📄 Pour sauvegarder en PDF :</h3>' +
                        '<ol>' +
                        '<li>Cliquez sur <strong>Fichier → Imprimer</strong> (ou Ctrl+P)</li>' +
                        '<li>Choisissez <strong>"Enregistrer en PDF"</strong> comme imprimante</li>' +
                        '<li>Cliquez sur <strong>Enregistrer</strong></li>' +
                        '</ol>' +
                        '<button onclick="window.print()" style="padding: 10px 20px; background: #4a90e2; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">🖨️ Imprimer maintenant</button>';
                    document.body.insertBefore(instructions, document.body.firstChild);
                };
                </script>
                </head>''')
                
                # Bouton de téléchargement HTML uniquement
                st.download_button(
                    label="📄 Format HTML",
                    data=html_for_print,
                    file_name=f"soumission_{result[1]}.html",
                    mime="text/html",
                    help="Téléchargez et ouvrez dans le navigateur pour imprimer"
                )
            
            # Afficher avec les boutons d'approbation si en attente
            from streamlit_compat import show_html
            if result[5] == 'en_attente':
                # Ajouter les boutons d'approbation
                html_with_buttons = html_content.replace(
                    '</body>',
                    f'''
                    <div style="position: fixed; bottom: 0; left: 0; right: 0; background: white; padding: 20px; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); display: flex; justify-content: center; gap: 20px;">
                        <a href="?token={token}&type=heritage&action=approve" style="padding: 15px 40px; background: linear-gradient(135deg, #48bb78 0%, #38a169 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; text-transform: uppercase;">
                            ✅ APPROUVER
                        </a>
                        <a href="?token={token}&type=heritage&action=reject" style="padding: 15px 40px; background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; text-transform: uppercase;">
                            ❌ REFUSER
                        </a>
                    </div>
                    </body>
                    '''
                )
                show_html(html_with_buttons, height=900, scrolling=True)
            else:
                show_html(html_content, height=800, scrolling=True)
            
        else:
            st.error("❌ Soumission non trouvée ou lien invalide")
            
    except Exception as e:
        st.error(f"Erreur: {e}")

def generate_pdf_from_html(html_content):
    """Génère un PDF à partir du HTML"""
    try:
        # Utiliser xhtml2pdf pour convertir HTML en PDF
        from xhtml2pdf import pisa
        from io import BytesIO
        
        # Nettoyer le HTML pour éviter les problèmes d'encodage
        import re
        html_content = html_content.replace('\u2019', "'")
        html_content = html_content.replace('\u201c', '"')
        html_content = html_content.replace('\u201d', '"')
        html_content = html_content.replace('\u2013', '-')
        html_content = html_content.replace('\u2014', '--')
        
        # Remplacer les variables CSS par des valeurs fixes
        css_replacements = {
            'var(--primary-color)': '#1e40af',
            'var(--secondary-color)': '#64748b',
            'var(--accent-color)': '#3b82f6',
            'var(--success-color)': '#22c55e',
            'var(--error-color)': '#ef4444',
            'var(--warning-color)': '#f59e0b',
            'var(--bg-primary)': '#ffffff',
            'var(--bg-secondary)': '#f8fafc',
            'var(--text-primary)': '#1e293b',
            'var(--text-secondary)': '#64748b',
            'var(--border-color)': '#e2e8f0'
        }
        
        for var_name, value in css_replacements.items():
            html_content = html_content.replace(var_name, value)
        
        # Remplacer toutes les autres variables CSS restantes par une couleur par défaut
        html_content = re.sub(r'var\\(--[^)]+\\)', '#333333', html_content)
        
        # Remplacer les fonctions CSS non supportées
        html_content = re.sub(r'linear-gradient\\([^)]+\\)', '#3b82f6', html_content)
        html_content = re.sub(r'radial-gradient\\([^)]+\\)', '#3b82f6', html_content)
        html_content = re.sub(r'rgba\\([^)]+\\)', '#333333', html_content)
        
        # Simplifier les box-shadow
        html_content = re.sub(r'box-shadow:[^;]+;', 'border: 1px solid #e2e8f0;', html_content)
        
        # Ajouter une balise meta pour l'encodage si elle n'existe pas
        if '<meta charset=' not in html_content.lower():
            html_content = html_content.replace(
                '<head>',
                '<head><meta charset="UTF-8">'
            )
        
        # Créer un buffer pour le PDF
        pdf_buffer = BytesIO()
        
        # Convertir HTML en PDF avec options améliorées
        pisa_status = pisa.CreatePDF(
            html_content.encode('utf-8'),
            dest=pdf_buffer,
            encoding='utf-8',
            link_callback=lambda uri, rel: uri  # Conserver les liens tels quels
        )
        
        # Récupérer le contenu PDF
        pdf_buffer.seek(0)
        pdf_data = pdf_buffer.read()
        pdf_buffer.close()
        
        if not pisa_status.err:
            return pdf_data
        else:
            return None
            
    except ImportError:
        # Si xhtml2pdf n'est pas disponible, essayer une méthode alternative
        try:
            # Retourner le HTML encodé comme fallback
            return html_content.encode('utf-8')
        except:
            return None
    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF: {e}")
        return None

def show_client_view(token):
    """Affiche la vue client multi-format"""
    submission = get_submission_by_token(token)
    
    if not submission:
        st.error("⚠️ Soumission non trouvée ou lien invalide")
        return
    
    # Vérifier si une action est demandée
    query_params = get_query_params()
    action = query_params.get('action', [None])[0]
    
    if action == 'approve' and submission['statut'] == 'en_attente':
        update_submission_status(token, 'approuvee')
        submission['statut'] = 'approuvee'
        set_query_params(token=token)
        st.success("✅ Soumission APPROUVÉE avec succès!")
        st.balloons()
        
    elif action == 'reject' and submission['statut'] == 'en_attente':
        update_submission_status(token, 'refusee')
        submission['statut'] = 'refusee'
        set_query_params(token=token)
        st.error("❌ Soumission REFUSÉE")
    
    
    # Créer et afficher la page d'approbation
    approval_html = create_approval_page(submission)
    show_html(approval_html, height=1500, scrolling=True)

def show_edit_form():
    """Affiche le formulaire d'édition universel pour toutes les soumissions"""
    st.header("✏️ Modifier la Soumission")
    
    if st.button("🔙 Retour au Dashboard"):
        if 'edit_heritage_id' in st.session_state:
            del st.session_state['edit_heritage_id']
        if 'edit_submission_id' in st.session_state:
            del st.session_state['edit_submission_id']
        rerun()
    
    # Déterminer quel type de soumission on édite
    heritage_id = st.session_state.get('edit_heritage_id')
    submission_id = st.session_state.get('edit_submission_id')
    
    if heritage_id:
        # Edition d'une soumission Heritage
        show_edit_heritage_form_internal(heritage_id)
    elif submission_id:
        # Edition d'une soumission uploadée
        show_edit_uploaded_form_internal(submission_id)
    else:
        st.error("Aucune soumission à modifier")

def show_edit_heritage_form_internal(submission_id):
    """Formulaire d'édition pour soumissions Heritage"""
    import sqlite3
    import json
    
    conn = sqlite3.connect('data/soumissions_heritage.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT numero, client_nom, projet_nom, montant_total, data, statut
        FROM soumissions_heritage 
        WHERE id = ?
    ''', (submission_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        st.error("Soumission non trouvée")
        return
    
    # Charger les données
    data = json.loads(result[4]) if result[4] else {}
    
    st.info(f"📝 Modification de la soumission Heritage **{result[0]}**")
    
    # Formulaire d'édition simplifié
    with st.form("edit_heritage"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Informations Client")
            client_nom = st.text_input("Nom du client", value=result[1] or "")
            client_adresse = st.text_input("Adresse", value=data.get('client', {}).get('adresse', ""))
            client_telephone = st.text_input("Téléphone", value=data.get('client', {}).get('telephone', ""))
            client_email = st.text_input("Email", value=data.get('client', {}).get('email', ""))
        
        with col2:
            st.subheader("🏗️ Informations Projet")
            projet_nom = st.text_input("Nom du projet", value=result[2] or "")
            projet_adresse = st.text_input("Adresse du projet", value=data.get('projet', {}).get('adresse', ""))
            
            # Statut
            statut_options = ['en_attente', 'approuvee', 'refusee']
            statut_labels = {'en_attente': '⏳ En attente', 'approuvee': '✅ Approuvée', 'refusee': '❌ Refusée'}
            current_statut = result[5] or 'en_attente'
            
            statut = st.selectbox(
                "Statut",
                options=statut_options,
                format_func=lambda x: statut_labels[x],
                index=statut_options.index(current_statut)
            )
        
        st.divider()
        
        # Note sur le montant
        montant = st.number_input("💰 Montant total ($)", value=float(result[3]), format="%.2f", step=100.0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Sauvegarder", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❌ Annuler", use_container_width=True):
                del st.session_state['edit_heritage_id']
                rerun()
        
        if submitted:
            # Mettre à jour les données
            data['client'] = data.get('client', {})
            data['projet'] = data.get('projet', {})
            data['client']['nom'] = client_nom
            data['client']['adresse'] = client_adresse
            data['client']['telephone'] = client_telephone
            data['client']['email'] = client_email
            data['projet']['nom'] = projet_nom
            data['projet']['adresse'] = projet_adresse
            
            # Sauvegarder
            try:
                conn = sqlite3.connect('data/soumissions_heritage.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE soumissions_heritage 
                    SET client_nom = ?, projet_nom = ?, montant_total = ?, data = ?, statut = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (client_nom, projet_nom, montant, json.dumps(data, ensure_ascii=False, default=str), statut, submission_id))
                
                conn.commit()
                conn.close()
                
                st.success("✅ Soumission Heritage mise à jour avec succès!")
                st.balloons()
                
                # Retour au dashboard après 2 secondes
                import time
                time.sleep(2)
                del st.session_state['edit_heritage_id']
                rerun()
                
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour: {e}")

def show_edit_uploaded_form_internal(submission_id):
    """Formulaire d'édition pour soumissions uploadées"""
    import sqlite3
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT numero_soumission, nom_client, email_client, telephone_client,
               nom_projet, montant_total, statut, file_name, file_type
        FROM soumissions
        WHERE id = ?
    ''', (submission_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        st.error("Soumission non trouvée")
        return
    
    st.info(f"📝 Modification de la soumission **{result[0]}** (Fichier: {result[7]})")
    
    with st.form("edit_uploaded"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Informations Client")
            nom_client = st.text_input("Nom du client", value=result[1] or "")
            email_client = st.text_input("Email", value=result[2] or "")
            telephone_client = st.text_input("Téléphone", value=result[3] or "")
        
        with col2:
            st.subheader("🏗️ Informations Projet")
            nom_projet = st.text_input("Nom du projet", value=result[4] or "")
            
            # Statut
            statut_options = ['en_attente', 'approuvee', 'refusee']
            statut_labels = {'en_attente': '⏳ En attente', 'approuvee': '✅ Approuvée', 'refusee': '❌ Refusée'}
            current_statut = result[6] or 'en_attente'
            
            statut = st.selectbox(
                "Statut",
                options=statut_options,
                format_func=lambda x: statut_labels[x],
                index=statut_options.index(current_statut)
            )
        
        st.divider()
        
        # Montant
        montant_total = st.number_input("💰 Montant total ($)", value=float(result[5] or 0), format="%.2f", step=100.0)
        
        st.caption(f"📄 Type de fichier: {result[8]} - {result[7]}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Sauvegarder", type="primary", use_container_width=True)
        
        with col2:
            if st.form_submit_button("❌ Annuler", use_container_width=True):
                del st.session_state['edit_submission_id']
                rerun()
        
        if submitted:
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE soumissions
                    SET nom_client = ?, email_client = ?, telephone_client = ?,
                        nom_projet = ?, montant_total = ?, statut = ?
                    WHERE id = ?
                ''', (nom_client, email_client, telephone_client, nom_projet, montant_total, statut, submission_id))
                
                conn.commit()
                conn.close()
                
                st.success("✅ Soumission mise à jour avec succès!")
                st.balloons()
                
                # Retour au dashboard après 2 secondes
                import time
                time.sleep(2)
                del st.session_state['edit_submission_id']
                rerun()
                
            except Exception as e:
                st.error(f"Erreur lors de la mise à jour: {e}")

def delete_submission(submission_id, is_heritage=False):
    """Supprime une soumission (Heritage ou uploadée)"""
    try:
        if is_heritage:
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM soumissions_heritage WHERE id = ?', (submission_id,))
        else:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM soumissions WHERE id = ?', (submission_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression: {e}")
        return False

def show_bon_commande_interface():
    """Interface complète de gestion des bons de commande"""
    if not BON_COMMANDE_AVAILABLE:
        st.error("❌ Module de bon de commande non disponible")
        return
    
    st.title("📋 Système de Gestion des Bons de Commande")
    
    # Initialiser la base de données
    init_bon_commande_db()
    
    # Onglets pour les différentes fonctions
    tab1, tab2, tab3 = st.tabs(["📝 Nouveau Bon", "📋 Gestionnaire", "📊 Liste des Bons"])
    
    with tab1:
        show_nouveau_bon_commande()
    
    with tab2:
        show_gestionnaire_bons()
    
    with tab3:
        show_liste_bons_commande()

def show_nouveau_bon_commande():
    """Interface pour créer un nouveau bon de commande"""
    st.subheader("📝 Nouveau Bon de Commande")
    
    # Générer automatiquement un numéro de bon
    nouveau_numero = generer_numero_bon()
    st.info(f"📋 Numéro de bon : **{nouveau_numero}**")
    
    # Afficher le template HTML interactif dans une iframe
    try:
        # Créer les données par défaut pour un nouveau bon
        default_data = {
            'numeroBon': nouveau_numero,
            'dateBon': datetime.now().strftime('%Y-%m-%d'),
            'entreprise': {},
            'fournisseur': {
                'nom': '', 'adresse': '', 'ville': '', 'codePostal': '',
                'tel': '', 'cell': '', 'contact': ''
            },
            'projet': {
                'nomClient': '', 'nomProjet': '', 'lieu': '',
                'refSoumission': '', 'chargeProjet': ''
            },
            'conditions': {
                'validite': '30 jours', 'paiement': 'Net 30 jours',
                'dateDebut': '', 'dateFin': ''
            },
            'signatures': {
                'auteur': '', 'dateAuteur': '',
                'fournisseur': '', 'dateFournisseur': ''
            },
            'items': [{
                'id': 1, 'number': 1, 'title': '', 'description': '',
                'quantity': 1, 'unit': 'unité', 'unitPrice': 0, 'total': 0
            }],
            'attachments': []
        }
        
        # Générer le HTML avec les données par défaut
        html_content = generer_html_bon_commande(default_data)
        
        if html_content:
            show_html(html_content, height=800, scrolling=True)
        else:
            st.error("Erreur lors de la génération du bon de commande")
    except Exception as e:
        st.error(f"Erreur : {str(e)}")
        st.info("Vérifiez que le fichier bon-commande-moderne.html existe dans le répertoire du projet.")

def show_gestionnaire_bons():
    """Interface de gestion des bons de commande existants"""
    st.subheader("📋 Gestionnaire de Bons de Commande")
    
    # Liste des bons existants pour sélection
    bons_list = lister_bons_commande()
    
    if not bons_list:
        st.info("Aucun bon de commande trouvé. Créez votre premier bon dans l'onglet 'Nouveau Bon'.")
        return
    
    # Sélecteur de bon
    bon_options = {f"{bon['numero_bon']} - {bon['fournisseur_nom'] or 'Sans nom'} ({bon['date_creation'][:10]})": bon['numero_bon'] 
                   for bon in bons_list}
    
    selected_display = st.selectbox("Choisir un bon de commande", list(bon_options.keys()))
    
    if selected_display:
        selected_numero = bon_options[selected_display]
        
        # Boutons d'action
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("👁️ Visualiser"):
                st.session_state['bc_view'] = selected_numero
                
        with col2:
            if st.button("✏️ Modifier"):
                st.session_state['bc_edit'] = selected_numero
                
        with col3:
            if st.button("📋 Dupliquer"):
                nouveau_numero = dupliquer_bon_commande(selected_numero)
                if nouveau_numero:
                    st.success(f"✅ Bon dupliqué ! Nouveau numéro : {nouveau_numero}")
                    st.balloons()
                else:
                    st.error("❌ Erreur lors de la duplication")
                
        with col4:
            if st.button("🗑️ Supprimer", type="secondary"):
                st.session_state['bc_delete'] = selected_numero
        
        # Gestion de l'affichage
        if 'bc_view' in st.session_state:
            show_bon_commande_viewer(st.session_state['bc_view'])
            
        elif 'bc_edit' in st.session_state:
            show_bon_commande_editor(st.session_state['bc_edit'])
            
        elif 'bc_delete' in st.session_state:
            show_bon_commande_delete_confirm(st.session_state['bc_delete'])

def show_bon_commande_viewer(numero_bon):
    """Affiche un bon de commande en mode lecture seule"""
    st.divider()
    st.subheader(f"👁️ Visualisation du Bon {numero_bon}")
    
    if st.button("🔙 Retour à la liste"):
        del st.session_state['bc_view']
        rerun()
    
    # Charger les données du bon
    data = charger_bon_commande(numero_bon)
    
    if data:
        # Générer le HTML avec les données
        html_content = generer_html_bon_commande(data)
        
        if html_content:
            show_html(html_content, height=800, scrolling=True)
        else:
            st.error("Erreur lors de la génération du HTML")
    else:
        st.error("❌ Bon de commande non trouvé")

def show_bon_commande_editor(numero_bon):
    """Affiche un bon de commande en mode édition"""
    st.divider()
    st.subheader(f"✏️ Modification du Bon {numero_bon}")
    
    if st.button("🔙 Retour à la liste"):
        del st.session_state['bc_edit']
        rerun()
    
    # Charger les données du bon
    data = charger_bon_commande(numero_bon)
    
    if data:
        # Générer le HTML avec les données (le HTML est interactif)
        html_content = generer_html_bon_commande(data)
        
        if html_content:
            show_html(html_content, height=800, scrolling=True)
            
            st.info("💡 Le bon de commande ci-dessus est interactif. Vous pouvez le modifier directement et utiliser les boutons de sauvegarde intégrés.")
        else:
            st.error("Erreur lors de la génération du HTML")
    else:
        st.error("❌ Bon de commande non trouvé")

def show_bon_commande_delete_confirm(numero_bon):
    """Confirmation de suppression d'un bon de commande"""
    st.divider()
    st.warning(f"⚠️ Êtes-vous sûr de vouloir supprimer le bon de commande **{numero_bon}** ?")
    st.error("Cette action est irréversible !")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Oui, supprimer", type="primary"):
            if supprimer_bon_commande(numero_bon):
                st.success(f"✅ Bon {numero_bon} supprimé avec succès !")
                del st.session_state['bc_delete']
                import time
                time.sleep(2)
                rerun()
            else:
                st.error("❌ Erreur lors de la suppression")
    
    with col2:
        if st.button("❌ Annuler"):
            del st.session_state['bc_delete']
            rerun()

def show_liste_bons_commande():
    """Affiche la liste de tous les bons de commande avec statistiques"""
    st.subheader("📊 Liste des Bons de Commande")
    
    bons_list = lister_bons_commande()
    
    if not bons_list:
        st.info("Aucun bon de commande trouvé.")
        return
    
    # Statistiques
    total_bons = len(bons_list)
    total_montant = sum(bon.get('total', 0) for bon in bons_list)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📋 Total Bons", total_bons)
    
    with col2:
        st.metric("💰 Montant Total", f"${total_montant:,.2f}")
    
    with col3:
        # Compter par statut si disponible
        brouillons = len([b for b in bons_list if b.get('statut') == 'brouillon'])
        st.metric("📝 Brouillons", brouillons)
    
    with col4:
        # Bons du mois courant
        from datetime import datetime
        mois_courant = datetime.now().strftime('%Y-%m')
        bons_mois = len([b for b in bons_list if b.get('date_creation', '').startswith(mois_courant)])
        st.metric("📅 Ce mois", bons_mois)
    
    st.divider()
    
    # Table des bons
    st.subheader("📋 Liste détaillée")
    
    # Filtres
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Rechercher", placeholder="Numéro, fournisseur, projet...")
    
    # Filtrer les résultats
    filtered_bons = bons_list
    if search:
        search = search.lower()
        filtered_bons = [
            bon for bon in bons_list
            if search in bon.get('numero_bon', '').lower() or 
               search in bon.get('fournisseur_nom', '').lower() or 
               search in bon.get('projet_nom', '').lower()
        ]
    
    # Affichage des bons
    for bon in filtered_bons:
        with st.expander(f"📋 **{bon['numero_bon']}** - {bon.get('fournisseur_nom') or 'Sans nom'} (${bon.get('total', 0):,.2f})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Fournisseur:** {bon.get('fournisseur_nom') or 'N/A'}")
                st.write(f"**Client:** {bon.get('client_nom') or 'N/A'}")
                st.write(f"**Projet:** {bon.get('projet_nom') or 'N/A'}")
            
            with col2:
                st.write(f"**Date création:** {bon.get('date_creation', 'N/A')[:10]}")
                st.write(f"**Dernière modif:** {bon.get('derniere_modification', 'N/A')[:10]}")
                st.write(f"**Statut:** {bon.get('statut', 'N/A').title()}")
            
            with col3:
                st.write(f"**Montant:** ${bon.get('total', 0):,.2f}")
                
                # Boutons d'action
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button(f"👁️ Voir", key=f"view_{bon['numero_bon']}"):
                        st.session_state['bc_view'] = bon['numero_bon']
                        rerun()
                with col_btn2:
                    if st.button(f"✏️ Modifier", key=f"edit_{bon['numero_bon']}"):
                        st.session_state['bc_edit'] = bon['numero_bon']
                        rerun()

def show_admin_dashboard():
    """Dashboard administrateur multi-format"""
    # Import du module de configuration d'entreprise
    try:
        from entreprise_config import show_entreprise_config, get_entreprise_config
        has_entreprise_config = True
        company_name = get_entreprise_config().get('nom', 'C2B Construction')
    except ImportError:
        has_entreprise_config = False
        company_name = 'C2B Construction'
    
    # Titre principal avec nom dynamique
    st.title(f"🏗️ {company_name} - Gestion Complète")
    st.caption("Upload, Modification et Suppression de Soumissions Multi-Format")
    
    # CSS pour améliorer l'apparence
    st.markdown("""
    <style>
        .file-type-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 5px;
        }
        .pdf-badge { background: #ff6b6b; color: white; }
        .doc-badge { background: #4dabf7; color: white; }
        .xls-badge { background: #51cf66; color: white; }
        .img-badge { background: #ffd43b; color: #333; }
        .html-badge { background: #845ef7; color: white; }
    </style>
    """, unsafe_allow_html=True)
    
    # Vérifier si on doit afficher le mode édition
    if 'edit_heritage_id' in st.session_state or 'edit_submission_id' in st.session_state:
        show_edit_form()
    else:
        # Tabs principaux - bien visibles avec Entreprise en premier
        if has_entreprise_config:
            if BON_COMMANDE_AVAILABLE:
                tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                    "🏢 **ENTREPRISE**",
                    "📋 **BONS DE COMMANDE**",
                    "📊 **TABLEAU DE BORD**", 
                    "➕ **CRÉER SOUMISSION HÉRITAGE**", 
                    "📤 **UPLOADER DOCUMENT**",
                    "💾 **SAUVEGARDES**"
                ])
            else:
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🏢 **ENTREPRISE**",
                    "📊 **TABLEAU DE BORD**", 
                    "➕ **CRÉER SOUMISSION HÉRITAGE**", 
                    "📤 **UPLOADER DOCUMENT**",
                    "💾 **SAUVEGARDES**"
                ])
        else:
            if BON_COMMANDE_AVAILABLE:
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "📋 **BONS DE COMMANDE**",
                    "📊 **TABLEAU DE BORD**", 
                    "➕ **CRÉER SOUMISSION HÉRITAGE**", 
                    "📤 **UPLOADER DOCUMENT**",
                    "💾 **SAUVEGARDES**"
                ])
            else:
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 **TABLEAU DE BORD**", 
                    "➕ **CRÉER SOUMISSION HÉRITAGE**", 
                    "📤 **UPLOADER DOCUMENT**",
                    "💾 **SAUVEGARDES**"
                ])
        
        if has_entreprise_config:
            with tab1:
                # Afficher la configuration de l'entreprise
                show_entreprise_config()
            
            if BON_COMMANDE_AVAILABLE:
                with tab2:
                    show_bon_commande_interface()
                
                with tab3:
                    show_dashboard_content()
                
                with tab4:
                    # Importer et afficher le module de création de soumission
                    try:
                        from soumission_heritage import show_soumission_heritage
                        show_soumission_heritage()
                    except Exception as e:
                        st.error(f"Erreur chargement module Heritage: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                with tab5:
                    show_upload_section()
                
                with tab6:
                    # Onglet de sauvegarde
                    import backup_manager
                    backup_manager.show_backup_interface()
            else:
                with tab2:
                    show_dashboard_content()
                
                with tab3:
                    # Importer et afficher le module de création de soumission
                    try:
                        from soumission_heritage import show_soumission_heritage
                        show_soumission_heritage()
                    except Exception as e:
                        st.error(f"Erreur chargement module Heritage: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                with tab4:
                    show_upload_section()
                
                with tab5:
                    # Onglet de sauvegarde
                    import backup_manager
                    backup_manager.show_backup_interface()
        else:
            if BON_COMMANDE_AVAILABLE:
                with tab1:
                    show_bon_commande_interface()
                
                with tab2:
                    show_dashboard_content()
                
                with tab3:
                    # Importer et afficher le module de création de soumission
                    try:
                        from soumission_heritage import show_soumission_heritage
                        show_soumission_heritage()
                    except Exception as e:
                        st.error(f"Erreur chargement module Heritage: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                with tab4:
                    show_upload_section()
                
                with tab5:
                    # Onglet de sauvegarde
                    import backup_manager
                    backup_manager.show_backup_interface()
            else:
                with tab1:
                    show_dashboard_content()
                
                with tab2:
                    # Importer et afficher le module de création de soumission
                    try:
                        from soumission_heritage import show_soumission_heritage
                        show_soumission_heritage()
                    except Exception as e:
                        st.error(f"Erreur chargement module Heritage: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                
                with tab3:
                    show_upload_section()
                
                with tab4:
                    # Onglet de sauvegarde
                    import backup_manager
                    backup_manager.show_backup_interface()

def show_upload_section():
    """Section d'upload de documents"""
    st.header("📤 Upload de Document")
    
    # Liste des formats supportés
    with st.expander("📋 Formats supportés", expanded=True):
        for category, exts in SUPPORTED_EXTENSIONS.items():
            st.write(f"**{category}:** {', '.join(exts)}")
    
    uploaded_file = st.file_uploader(
        "Choisir un document",
        type=[ext.replace('.', '') for ext in ALL_EXTENSIONS],
        help="Uploadez votre soumission dans n'importe quel format supporté"
    )
    
    if uploaded_file:
        file_type = get_file_type(uploaded_file)
        
        st.success(f"✅ Fichier détecté: **{file_type['category']}**")
        st.info(f"📄 {file_type['name']} ({uploaded_file.size/1024:.1f} KB)")
        
        # Extraction automatique ou manuelle
        st.subheader("📝 Informations de la soumission")
        
        # Numéro automatique
        numero = get_next_submission_number()
        st.info(f"🔢 Numéro: **{numero}**")
        
        # Tentative d'extraction automatique
        if file_type['extension'] in ['.pdf', '.html', '.htm']:
            with st.spinner("Extraction automatique en cours..."):
                nom_client, nom_projet, montant = extract_info_from_file(uploaded_file, file_type)
                uploaded_file.seek(0)  # Reset file pointer
        else:
            nom_client, nom_projet, montant = "Client", "Projet", 0.0
        
        # Formulaire d'édition
        with st.form("submission_form"):
            nom_client = st.text_input("Nom du client", value=nom_client)
            email_client = st.text_input("Email", placeholder="client@exemple.com")
            tel_client = st.text_input("Téléphone", placeholder="514-123-4567")
            nom_projet = st.text_input("Nom du projet", value=nom_projet)
            montant = st.number_input("Montant total ($)", value=float(montant), format="%.2f", step=100.0)
            
            if st.form_submit_button("💾 Sauvegarder et Générer le Lien", type="primary"):
                try:
                    # Reset file pointer before saving
                    uploaded_file.seek(0)
                    
                    sub_id, token, lien = save_submission_multi(
                        numero, nom_client, email_client, tel_client,
                        nom_projet, montant, uploaded_file, file_type
                    )
                    
                    st.success("✅ Document sauvegardé avec succès!")
                    st.info(f"🔗 Lien client:")
                    st.code(lien, language=None)
                    
                    st.balloons()
                    
                    # Attendre avant de recharger
                    import time
                    time.sleep(2)
                    rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

def show_dashboard_content():
    """Affiche le contenu du dashboard principal"""
    st.subheader("📊 Tableau de Bord des Soumissions")
    
    submissions = get_all_submissions()
    
    if submissions:
        # Statistiques
        col1, col2, col3, col4, col5 = st.columns(5)
        
        total = len(submissions)
        en_attente = len([s for s in submissions if s['statut'] == 'en_attente'])
        approuvees = len([s for s in submissions if s['statut'] == 'approuvee'])
        refusees = len([s for s in submissions if s['statut'] == 'refusee'])
        
        # Compter par type
        pdf_count = len([s for s in submissions if s['file_type'] == '.pdf'])
        
        with col1:
            st.metric("📁 Total", total)
        with col2:
            st.metric("⏳ En attente", en_attente)
        with col3:
            st.metric("✅ Approuvées", approuvees)
        with col4:
            st.metric("❌ Refusées", refusees)
        with col5:
            st.metric("📄 PDF", pdf_count)
        
        st.divider()
        
        # Filtres
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search = st.text_input("🔍 Rechercher", placeholder="Numéro, client, projet...")
        with col2:
            filtre_statut = st.selectbox("Statut", ["Tous", "En attente", "Approuvée", "Refusée"])
        with col3:
            filtre_type = st.selectbox("Type", ["Tous"] + list(set([s['file_type'] for s in submissions])))
        
        # Filtrer
        filtered = submissions
        
        if search:
            search = search.lower()
            filtered = [s for s in filtered if 
                       search in s['numero'].lower() or 
                       search in s['client'].lower() or 
                       search in (s['projet'] or '').lower()]
        
        if filtre_statut != "Tous":
            statut_map = {"En attente": "en_attente", "Approuvée": "approuvee", "Refusée": "refusee"}
            filtered = [s for s in filtered if s['statut'] == statut_map[filtre_statut]]
        
        if filtre_type != "Tous":
            filtered = [s for s in filtered if s['file_type'] == filtre_type]
        
        # Afficher les soumissions
        st.subheader(f"📋 Soumissions ({len(filtered)})")
        
        for sub in filtered:
            # Badge pour le type de fichier
            type_badges = {
                '.pdf': 'pdf-badge',
                '.doc': 'doc-badge', '.docx': 'doc-badge',
                '.xls': 'xls-badge', '.xlsx': 'xls-badge',
                '.jpg': 'img-badge', '.jpeg': 'img-badge', '.png': 'img-badge',
                '.html': 'html-badge', '.htm': 'html-badge'
            }
            badge_class = type_badges.get(sub['file_type'], '')
            
            status_icon = {
                'en_attente': '⏳',
                'approuvee': '✅',
                'refusee': '❌'
            }.get(sub['statut'], '❓')
            
            # Ajouter un indicateur pour les soumissions Heritage
            source_label = " 🏗️ [Heritage]" if sub.get('source') == 'heritage' else ""
            
            with st.expander(f"{status_icon} **{sub['numero']}** - {sub['client']} - {sub['projet'] or 'Sans nom'}{source_label}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Client:** {sub['client']}")
                    if sub.get('email'):
                        st.write(f"**Email:** {sub['email']}")
                    st.write(f"**Projet:** {sub['projet'] or 'N/A'}")
                    st.write(f"**Montant:** ${sub['montant']:,.2f}")
                
                with col2:
                    st.write(f"**Statut:** {status_icon} {sub['statut'].replace('_', ' ').title()}")
                    st.write(f"**Date:** {sub['date_creation'][:10] if sub['date_creation'] else 'N/A'}")
                    st.write(f"**Fichier:** {sub['file_name']}")
                    st.markdown(f"**Type:** <span class='file-type-badge {badge_class}'>{sub['file_type']}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.write("**Lien client:**")
                    st.code(sub['lien'], language=None)
                    
                    # Boutons d'actions
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if sub.get('source') == 'heritage':
                            # Pour les soumissions Heritage, ouvrir directement le HTML
                            if st.button(f"📄 Voir", key=f"view_{sub['id']}"):
                                # Récupérer les données de la soumission Heritage
                                import soumission_heritage
                                heritage_id = sub['id'][1:]  # Enlever le préfixe 'H'
                                html_content = soumission_heritage.get_saved_submission_html(int(heritage_id))
                                if html_content:
                                    st.session_state['heritage_html'] = html_content
                                    st.session_state['show_heritage'] = True
                                    rerun()
                        else:
                            if st.button(f"👁️ Voir", key=f"view_{sub['id']}"):
                                st.session_state['view_token'] = sub['lien'].split('token=')[1] if 'token=' in sub['lien'] else None
                                rerun()
                    
                    # Boutons modifier et supprimer pour TOUTES les soumissions
                    with col_btn2:
                        if st.button(f"✏️ Modifier", key=f"edit_{sub['id']}"):
                            if sub.get('source') == 'heritage':
                                st.session_state['edit_heritage_id'] = int(sub['id'][1:])
                            else:
                                st.session_state['edit_submission_id'] = int(sub['id'])
                            st.session_state['active_tab'] = 'edit'
                            rerun()
                    
                    with col_btn3:
                        if st.button(f"🗑️ Suppr.", key=f"delete_{sub['id']}", type="secondary"):
                            if sub.get('source') == 'heritage':
                                st.session_state['delete_heritage_id'] = int(sub['id'][1:])
                                st.session_state['delete_is_heritage'] = True
                            else:
                                st.session_state['delete_submission_id'] = int(sub['id'])
                                st.session_state['delete_is_heritage'] = False
                            st.session_state['show_delete_confirm'] = True
                            rerun()
    else:
        st.info("🚫 Aucune soumission. Uploadez votre premier document!")

def main():
    """Fonction principale"""
    init_database()
    
    # Gérer la suppression avec confirmation
    if 'show_delete_confirm' in st.session_state and st.session_state.get('show_delete_confirm'):
        st.warning("⚠️ Êtes-vous sûr de vouloir supprimer cette soumission ?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Oui, supprimer", type="primary"):
                # Déterminer quel type de soumission supprimer
                if st.session_state.get('delete_is_heritage'):
                    delete_submission(st.session_state.get('delete_heritage_id'), is_heritage=True)
                    if 'delete_heritage_id' in st.session_state:
                        del st.session_state['delete_heritage_id']
                else:
                    delete_submission(st.session_state.get('delete_submission_id'), is_heritage=False)
                    if 'delete_submission_id' in st.session_state:
                        del st.session_state['delete_submission_id']
                
                del st.session_state['show_delete_confirm']
                if 'delete_is_heritage' in st.session_state:
                    del st.session_state['delete_is_heritage']
                    
                st.success("✅ Soumission supprimée avec succès!")
                st.balloons()
                import time
                time.sleep(2)
                rerun()
        with col2:
            if st.button("❌ Annuler"):
                del st.session_state['show_delete_confirm']
                if 'delete_heritage_id' in st.session_state:
                    del st.session_state['delete_heritage_id']
                if 'delete_submission_id' in st.session_state:
                    del st.session_state['delete_submission_id']
                if 'delete_is_heritage' in st.session_state:
                    del st.session_state['delete_is_heritage']
                rerun()
        return
    
    # Router
    query_params = get_query_params()
    token = query_params.get('token', [None])[0]
    type_param = query_params.get('type', [None])[0]
    action = query_params.get('action', [None])[0]
    
    # Gérer les actions d'approbation/refus pour Heritage
    if token and type_param == 'heritage' and action:
        import sqlite3
        conn = sqlite3.connect('data/soumissions_heritage.db')
        cursor = conn.cursor()
        
        if action == 'approve':
            cursor.execute('''
                UPDATE soumissions_heritage 
                SET statut = 'approuvee', updated_at = CURRENT_TIMESTAMP
                WHERE token = ?
            ''', (token,))
            conn.commit()
            st.success("✅ Soumission approuvée avec succès!")
        elif action == 'reject':
            cursor.execute('''
                UPDATE soumissions_heritage 
                SET statut = 'refusee', updated_at = CURRENT_TIMESTAMP
                WHERE token = ?
            ''', (token,))
            conn.commit()
            st.error("❌ Soumission refusée")
        
        conn.close()
        # Rediriger vers la vue sans action
        set_query_params(token=token, type='heritage')
    
    # Preview mode Heritage
    if 'show_heritage' in st.session_state and st.session_state.get('show_heritage'):
        if 'heritage_html' in st.session_state:
            st.markdown("### 📄 Visualisation de la Soumission Heritage")
            from streamlit_compat import show_html
            show_html(st.session_state['heritage_html'], height=800, scrolling=True)
            if st.button("🔙 Retour au Dashboard"):
                del st.session_state['show_heritage']
                del st.session_state['heritage_html']
                rerun()
        else:
            st.error("Erreur : Impossible de charger la soumission")
            if st.button("🔙 Retour"):
                del st.session_state['show_heritage']
                rerun()
    # Preview mode
    elif 'view_token' in st.session_state and st.session_state['view_token']:
        show_client_view(st.session_state['view_token'])
        if st.button("🔙 Retour au Dashboard"):
            del st.session_state['view_token']
            rerun()
    # Client view
    elif token:
        if type_param == 'heritage':
            # Afficher une soumission Heritage avec le token
            show_heritage_client_view(token)
        else:
            show_client_view(token)
    else:
        # Admin view
        if 'authenticated' not in st.session_state:
            st.session_state['authenticated'] = False
        
        if not st.session_state['authenticated']:
            # Login
            st.markdown("""
            <div style="max-width: 400px; margin: 100px auto; padding: 40px; background: white; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.1);">
                <h2 style="text-align: center; color: #2d3748;">🔐 Connexion Admin</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("login"):
                    password = st.text_input("Mot de passe", type="password")
                    if st.form_submit_button("Se connecter", type="primary", use_container_width=True):
                        if password == ADMIN_PASSWORD:
                            st.session_state['authenticated'] = True
                            rerun()
                        else:
                            st.error("❌ Mot de passe incorrect")
        else:
            # Admin dashboard
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("🚪 Déconnexion"):
                    st.session_state['authenticated'] = False
                    rerun()
            
            show_admin_dashboard()

if __name__ == "__main__":
    main()