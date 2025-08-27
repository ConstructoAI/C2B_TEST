"""
Module de gestion de la configuration d'entreprise
Permet la personnalisation complète des informations d'entreprise
"""

import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import base64
from pathlib import Path

# Configuration par défaut (Construction Héritage comme template)
DEFAULT_CONFIG = {
    'nom': 'Construction Héritage',
    'adresse': '129 Rue Poirier',
    'ville': 'Saint-Jean-sur-Richelieu',
    'province': 'Québec',
    'code_postal': 'J3B 4E9',
    'telephone_bureau': '438-524-9193',
    'telephone_cellulaire': '514-983-7492',
    'email': 'info@constructionheritage.ca',
    'site_web': 'www.constructionheritage.ca',
    'rbq': '5788-9784-01',
    'neq': '1163835623',
    'tps': '850370164RT0001',
    'tvq': '1212199610TQ0002',
    'contact_principal_nom': '',
    'contact_principal_titre': '',
    'contact_principal_telephone': '',
    'contact_principal_email': '',
    'logo_path': '',
    'logo_base64': '',
    'couleur_primaire': '#374151',
    'couleur_secondaire': '#4b5563',
    'couleur_accent': '#3b82f6',
    'slogan': '',
    'conditions_paiement': '30% à la signature, 35% début des travaux, paiements progressifs selon avancement, 35% retenue finale',
    'garanties': '1 an main-d\'œuvre, 5 ans toiture, 10 ans structure, selon normes GCR',
    'delai_validite_soumission': '30',
    'taux_administration': 3.0,
    'taux_contingences': 12.0,
    'taux_profit': 15.0
}

def init_entreprise_table():
    """Initialise la table de configuration d'entreprise"""
    db_path = 'data/entreprise_config.db'
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entreprise_config (
            id INTEGER PRIMARY KEY,
            config_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Vérifier si une configuration existe
    cursor.execute('SELECT COUNT(*) FROM entreprise_config')
    count = cursor.fetchone()[0]
    
    # Si aucune config, insérer la config par défaut
    if count == 0:
        cursor.execute('''
            INSERT INTO entreprise_config (config_data)
            VALUES (?)
        ''', (json.dumps(DEFAULT_CONFIG, ensure_ascii=False),))
    
    conn.commit()
    conn.close()

def get_entreprise_config():
    """Récupère la configuration actuelle de l'entreprise"""
    try:
        db_path = 'data/entreprise_config.db'
        
        # Si la base n'existe pas, l'initialiser
        if not os.path.exists(db_path):
            init_entreprise_table()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT config_data FROM entreprise_config
            ORDER BY id DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        else:
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        print(f"Erreur lors de la récupération de la config: {e}")
        return DEFAULT_CONFIG.copy()

def save_entreprise_config(config_data):
    """Sauvegarde la configuration de l'entreprise"""
    try:
        db_path = 'data/entreprise_config.db'
        
        # S'assurer que la table existe
        if not os.path.exists(db_path):
            init_entreprise_table()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Mettre à jour ou insérer
        cursor.execute('SELECT COUNT(*) FROM entreprise_config')
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute('''
                UPDATE entreprise_config 
                SET config_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = (SELECT MAX(id) FROM entreprise_config)
            ''', (json.dumps(config_data, ensure_ascii=False),))
        else:
            cursor.execute('''
                INSERT INTO entreprise_config (config_data)
                VALUES (?)
            ''', (json.dumps(config_data, ensure_ascii=False),))
        
        conn.commit()
        conn.close()
        
        return True, "Configuration sauvegardée avec succès!"
    except Exception as e:
        return False, f"Erreur lors de la sauvegarde: {str(e)}"

def process_logo_upload(uploaded_file):
    """Traite l'upload d'un logo et le convertit en base64"""
    if uploaded_file is not None:
        # Lire le fichier
        bytes_data = uploaded_file.getbuffer()
        
        # Convertir en base64
        logo_base64 = base64.b64encode(bytes_data).decode()
        
        # Déterminer le type MIME
        file_extension = uploaded_file.name.split('.')[-1].lower()
        mime_types = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml'
        }
        mime_type = mime_types.get(file_extension, 'image/png')
        
        # Créer la chaîne data URL complète
        logo_data_url = f"data:{mime_type};base64,{logo_base64}"
        
        return logo_data_url
    return None

def show_entreprise_config():
    """Affiche l'interface de configuration de l'entreprise"""
    st.header("🏢 Configuration de l'Entreprise")
    st.markdown("Personnalisez les informations de votre entreprise qui apparaîtront dans toutes les soumissions.")
    
    # Charger la configuration actuelle
    config = get_entreprise_config()
    
    # Initialiser session state si nécessaire
    if 'entreprise_config' not in st.session_state:
        st.session_state.entreprise_config = config.copy()
    
    # CSS pour améliorer l'apparence
    st.markdown("""
    <style>
        .config-section {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #3b82f6;
        }
        .section-title {
            font-size: 18px;
            font-weight: 600;
            color: #1e40af;
            margin-bottom: 15px;
        }
        .success-message {
            background: #d1fae5;
            color: #065f46;
            padding: 10px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.form("entreprise_config_form"):
        # Section 1: Informations de base
        st.markdown('<div class="section-title">📍 Informations de base</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom de l'entreprise *", value=config.get('nom', ''), key="nom_entreprise")
            adresse = st.text_input("Adresse", value=config.get('adresse', ''))
            ville = st.text_input("Ville", value=config.get('ville', ''))
        
        with col2:
            province = st.selectbox("Province", 
                                   options=['Québec', 'Ontario', 'Alberta', 'Colombie-Britannique', 'Manitoba', 
                                          'Nouveau-Brunswick', 'Terre-Neuve-et-Labrador', 'Nouvelle-Écosse', 
                                          'Île-du-Prince-Édouard', 'Saskatchewan'],
                                   index=0 if config.get('province', 'Québec') == 'Québec' else None)
            code_postal = st.text_input("Code postal", value=config.get('code_postal', ''))
            site_web = st.text_input("Site web", value=config.get('site_web', ''))
        
        st.divider()
        
        # Section 2: Contact
        st.markdown('<div class="section-title">📞 Coordonnées</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            telephone_bureau = st.text_input("Téléphone bureau", value=config.get('telephone_bureau', ''))
            telephone_cellulaire = st.text_input("Téléphone cellulaire", value=config.get('telephone_cellulaire', ''))
        
        with col2:
            email = st.text_input("Courriel", value=config.get('email', ''))
            slogan = st.text_input("Slogan (optionnel)", value=config.get('slogan', ''))
        
        st.divider()
        
        # Section 3: Informations légales
        st.markdown('<div class="section-title">📋 Informations légales</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            rbq = st.text_input("Numéro RBQ", value=config.get('rbq', ''), 
                               help="Régie du bâtiment du Québec")
            neq = st.text_input("Numéro NEQ", value=config.get('neq', ''),
                               help="Numéro d'entreprise du Québec")
        
        with col2:
            tps = st.text_input("Numéro TPS", value=config.get('tps', ''),
                               help="Taxe sur les produits et services")
            tvq = st.text_input("Numéro TVQ", value=config.get('tvq', ''),
                               help="Taxe de vente du Québec")
        
        st.divider()
        
        # Section 4: Contact principal
        st.markdown('<div class="section-title">👤 Contact principal</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            contact_principal_nom = st.text_input("Nom du contact", value=config.get('contact_principal_nom', ''))
            contact_principal_titre = st.text_input("Titre/Poste", value=config.get('contact_principal_titre', ''))
        
        with col2:
            contact_principal_telephone = st.text_input("Téléphone du contact", 
                                                       value=config.get('contact_principal_telephone', ''))
            contact_principal_email = st.text_input("Courriel du contact", 
                                                   value=config.get('contact_principal_email', ''))
        
        st.divider()
        
        # Section 5: Logo et personnalisation visuelle
        st.markdown('<div class="section-title">🎨 Personnalisation visuelle</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            logo_file = st.file_uploader("Logo de l'entreprise", 
                                        type=['png', 'jpg', 'jpeg', 'gif', 'svg'],
                                        help="Format recommandé: PNG transparent, 500x200px max")
            
            # Afficher le logo actuel s'il existe
            if config.get('logo_base64'):
                st.markdown("**Logo actuel:**")
                st.markdown(f'<img src="{config.get("logo_base64")}" style="max-width: 200px;">', 
                          unsafe_allow_html=True)
        
        with col2:
            couleur_primaire = st.color_picker("Couleur primaire", value=config.get('couleur_primaire', '#374151'))
            couleur_accent = st.color_picker("Couleur d'accent", value=config.get('couleur_accent', '#3b82f6'))
        
        with col3:
            couleur_secondaire = st.color_picker("Couleur secondaire", value=config.get('couleur_secondaire', '#4b5563'))
            st.markdown("**Aperçu des couleurs:**")
            st.markdown(f'''
                <div style="display: flex; gap: 5px;">
                    <div style="width: 40px; height: 40px; background: {couleur_primaire}; border-radius: 5px;"></div>
                    <div style="width: 40px; height: 40px; background: {couleur_secondaire}; border-radius: 5px;"></div>
                    <div style="width: 40px; height: 40px; background: {couleur_accent}; border-radius: 5px;"></div>
                </div>
            ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Section 6: Paramètres commerciaux
        st.markdown('<div class="section-title">💼 Paramètres commerciaux</div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            delai_validite = st.number_input("Validité soumission (jours)", 
                                            min_value=7, max_value=365, 
                                            value=int(config.get('delai_validite_soumission', 30)))
        
        with col2:
            taux_administration = st.number_input("Taux admin. (%)", 
                                                 min_value=0.0, max_value=20.0, 
                                                 value=float(config.get('taux_administration', 3.0)),
                                                 step=0.5)
        
        with col3:
            taux_contingences = st.number_input("Taux contingences (%)", 
                                               min_value=0.0, max_value=30.0, 
                                               value=float(config.get('taux_contingences', 12.0)),
                                               step=0.5)
        
        with col4:
            taux_profit = st.number_input("Taux profit (%)", 
                                         min_value=0.0, max_value=50.0, 
                                         value=float(config.get('taux_profit', 15.0)),
                                         step=0.5)
        
        # Conditions et garanties
        conditions_paiement = st.text_area("Modalités de paiement", 
                                          value=config.get('conditions_paiement', ''),
                                          height=80)
        
        garanties = st.text_area("Garanties offertes", 
                                value=config.get('garanties', ''),
                                height=80)
        
        st.divider()
        
        # Boutons d'action
        col1, col2, col3 = st.columns(3)
        
        with col1:
            submitted = st.form_submit_button("💾 Sauvegarder la configuration", 
                                             type="primary", 
                                             use_container_width=True)
        
        with col2:
            reset = st.form_submit_button("🔄 Réinitialiser aux valeurs par défaut", 
                                         use_container_width=True)
        
        with col3:
            export = st.form_submit_button("📥 Exporter la configuration", 
                                         use_container_width=True)
    
    # Traitement des actions
    if submitted:
        # Créer le dictionnaire de configuration
        new_config = {
            'nom': nom,
            'adresse': adresse,
            'ville': ville,
            'province': province,
            'code_postal': code_postal,
            'telephone_bureau': telephone_bureau,
            'telephone_cellulaire': telephone_cellulaire,
            'email': email,
            'site_web': site_web,
            'rbq': rbq,
            'neq': neq,
            'tps': tps,
            'tvq': tvq,
            'contact_principal_nom': contact_principal_nom,
            'contact_principal_titre': contact_principal_titre,
            'contact_principal_telephone': contact_principal_telephone,
            'contact_principal_email': contact_principal_email,
            'couleur_primaire': couleur_primaire,
            'couleur_secondaire': couleur_secondaire,
            'couleur_accent': couleur_accent,
            'slogan': slogan,
            'conditions_paiement': conditions_paiement,
            'garanties': garanties,
            'delai_validite_soumission': str(delai_validite),
            'taux_administration': taux_administration,
            'taux_contingences': taux_contingences,
            'taux_profit': taux_profit
        }
        
        # Traiter le logo si un nouveau est uploadé
        if logo_file is not None:
            logo_data = process_logo_upload(logo_file)
            if logo_data:
                new_config['logo_base64'] = logo_data
        else:
            # Garder l'ancien logo s'il existe
            new_config['logo_base64'] = config.get('logo_base64', '')
        
        # Sauvegarder la configuration
        success, message = save_entreprise_config(new_config)
        
        if success:
            st.success(f"✅ {message}")
            st.balloons()
            # Mettre à jour le session state
            st.session_state.entreprise_config = new_config
            # Forcer le rechargement pour appliquer les changements
            st.rerun()
        else:
            st.error(f"❌ {message}")
    
    elif reset:
        # Réinitialiser aux valeurs par défaut
        success, message = save_entreprise_config(DEFAULT_CONFIG)
        if success:
            st.warning("⚠️ Configuration réinitialisée aux valeurs par défaut")
            st.session_state.entreprise_config = DEFAULT_CONFIG.copy()
            st.rerun()
    
    elif export:
        # Exporter la configuration en JSON
        config_json = json.dumps(config, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 Télécharger la configuration",
            data=config_json,
            file_name=f"config_entreprise_{config.get('nom', 'export').replace(' ', '_')}.json",
            mime="application/json"
        )

def import_entreprise_config():
    """Interface pour importer une configuration"""
    st.subheader("📤 Importer une configuration")
    
    uploaded_file = st.file_uploader("Choisir un fichier de configuration JSON", type=['json'])
    
    if uploaded_file is not None:
        try:
            config_data = json.load(uploaded_file)
            
            # Valider que c'est bien une config valide
            required_keys = ['nom', 'email', 'telephone_bureau']
            if all(key in config_data for key in required_keys):
                if st.button("📥 Importer cette configuration"):
                    success, message = save_entreprise_config(config_data)
                    if success:
                        st.success("✅ Configuration importée avec succès!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                
                # Afficher un aperçu
                with st.expander("Aperçu de la configuration à importer"):
                    st.json(config_data)
            else:
                st.error("❌ Le fichier ne contient pas une configuration valide")
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du fichier: {str(e)}")

# Fonction utilitaire pour obtenir les infos formatées
def get_formatted_company_info():
    """Retourne les informations de l'entreprise formatées pour l'affichage"""
    config = get_entreprise_config()
    
    formatted = {
        'header': f"{config.get('nom', 'Entreprise')}",
        'address_block': f"{config.get('adresse', '')}\n{config.get('ville', '')} ({config.get('province', 'Québec')}) {config.get('code_postal', '')}",
        'phone_block': f"T: {config.get('telephone_bureau', '')}",
        'email': config.get('email', ''),
        'legal_block': f"RBQ : {config.get('rbq', '')} | NEQ : {config.get('neq', '')}",
        'tax_block': f"TPS: {config.get('tps', '')} | TVQ: {config.get('tvq', '')}",
        'full_address': f"{config.get('adresse', '')}, {config.get('ville', '')} ({config.get('province', 'Québec')}) {config.get('code_postal', '')}",
        'contact': {
            'name': config.get('contact_principal_nom', ''),
            'title': config.get('contact_principal_titre', ''),
            'phone': config.get('contact_principal_telephone', config.get('telephone_bureau', '')),
            'email': config.get('contact_principal_email', config.get('email', ''))
        }
    }
    
    # Ajouter le téléphone cellulaire s'il existe
    if config.get('telephone_cellulaire'):
        formatted['phone_block'] += f" | C: {config.get('telephone_cellulaire', '')}"
    
    return formatted

def get_company_colors():
    """Retourne les couleurs de l'entreprise"""
    config = get_entreprise_config()
    return {
        'primary': config.get('couleur_primaire', '#374151'),
        'secondary': config.get('couleur_secondaire', '#4b5563'),
        'accent': config.get('couleur_accent', '#3b82f6')
    }

def get_company_logo():
    """Retourne le logo de l'entreprise en base64"""
    config = get_entreprise_config()
    return config.get('logo_base64', '')

def get_commercial_params():
    """Retourne les paramètres commerciaux"""
    config = get_entreprise_config()
    return {
        'taux_administration': float(config.get('taux_administration', 3.0)),
        'taux_contingences': float(config.get('taux_contingences', 12.0)),
        'taux_profit': float(config.get('taux_profit', 15.0)),
        'delai_validite': int(config.get('delai_validite_soumission', 30)),
        'conditions_paiement': config.get('conditions_paiement', ''),
        'garanties': config.get('garanties', '')
    }

# Initialiser la base de données au chargement du module
if __name__ != "__main__":
    init_entreprise_table()