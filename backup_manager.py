"""
Gestionnaire de sauvegarde pour les bases de données
"""
import os
import sqlite3
import zipfile
import json
from datetime import datetime
import streamlit as st

def create_backup():
    """Crée une sauvegarde complète des bases de données"""
    backup_data = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'databases': {}
    }
    
    # Sauvegarder la base Heritage
    if os.path.exists('data/soumissions_heritage.db'):
        try:
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            
            # Vérifier si la table existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='soumissions_heritage'
            """)
            
            if cursor.fetchone():
                cursor.execute("SELECT * FROM soumissions_heritage")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                backup_data['databases']['heritage'] = {
                    'columns': columns,
                    'data': rows
                }
            conn.close()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde Heritage: {e}")
    
    # Sauvegarder la base Multi-format
    if os.path.exists('data/soumissions_multi.db'):
        try:
            conn = sqlite3.connect('data/soumissions_multi.db')
            cursor = conn.cursor()
            
            # Vérifier si la table existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='soumissions'
            """)
            
            if cursor.fetchone():
                cursor.execute("SELECT * FROM soumissions")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                backup_data['databases']['multi'] = {
                    'columns': columns,
                    'data': rows
                }
            conn.close()
        except Exception as e:
            print(f"Erreur lors de la sauvegarde Multi-format: {e}")
    
    # Créer un fichier ZIP avec toutes les données
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    with zipfile.ZipFile(backup_filename, 'w') as zipf:
        # Ajouter le JSON de backup
        zipf.writestr('backup_data.json', json.dumps(backup_data, default=str, indent=2))
        
        # Ajouter les bases de données si elles existent
        if os.path.exists('data/soumissions_heritage.db'):
            zipf.write('data/soumissions_heritage.db', 'soumissions_heritage.db')
        if os.path.exists('data/soumissions_multi.db'):
            zipf.write('data/soumissions_multi.db', 'soumissions_multi.db')
        
        # Ajouter les fichiers uploadés
        uploads_dir = 'data/uploads'
        if os.path.exists(uploads_dir):
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, 'data')
                    zipf.write(file_path, arcname)
    
    return backup_filename

def restore_backup(backup_file):
    """Restaure une sauvegarde"""
    try:
        # Créer le répertoire data s'il n'existe pas
        os.makedirs('data', exist_ok=True)
        os.makedirs('data/uploads', exist_ok=True)
        
        # Extraire le fichier ZIP
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            # Extraire les bases de données
            for file in zipf.namelist():
                if file.endswith('.db'):
                    zipf.extract(file, 'data/')
                elif file.startswith('uploads/'):
                    zipf.extract(file, 'data/')
        
        return True, "Restauration réussie!"
    except Exception as e:
        return False, f"Erreur lors de la restauration: {str(e)}"

def show_backup_interface():
    """Interface de gestion des sauvegardes"""
    st.subheader("🔧 Gestion des sauvegardes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Télécharger une sauvegarde")
        st.markdown("Créez une sauvegarde complète de toutes vos données")
        
        if st.button("🔽 Créer et télécharger la sauvegarde", type="primary"):
            with st.spinner("Création de la sauvegarde..."):
                try:
                    backup_file = create_backup()
                    with open(backup_file, 'rb') as f:
                        st.download_button(
                            label="💾 Télécharger la sauvegarde",
                            data=f.read(),
                            file_name=backup_file,
                            mime="application/zip"
                        )
                    # Nettoyer le fichier temporaire
                    os.remove(backup_file)
                    st.success("✅ Sauvegarde créée avec succès!")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
    
    with col2:
        st.markdown("### 📤 Restaurer une sauvegarde")
        st.markdown("Restaurez vos données à partir d'une sauvegarde")
        
        uploaded_file = st.file_uploader(
            "Choisissez un fichier de sauvegarde (.zip)",
            type=['zip']
        )
        
        if uploaded_file is not None:
            if st.button("🔄 Restaurer la sauvegarde"):
                with st.spinner("Restauration en cours..."):
                    # Sauvegarder temporairement le fichier uploadé
                    temp_file = f"temp_{uploaded_file.name}"
                    with open(temp_file, 'wb') as f:
                        f.write(uploaded_file.getbuffer())
                    
                    success, message = restore_backup(temp_file)
                    
                    # Nettoyer le fichier temporaire
                    os.remove(temp_file)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                    else:
                        st.error(f"❌ {message}")
    
    # Informations sur l'état actuel
    st.markdown("---")
    st.markdown("### 📊 État actuel des données")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if os.path.exists('data/soumissions_heritage.db'):
            try:
                conn = sqlite3.connect('data/soumissions_heritage.db')
                cursor = conn.cursor()
                
                # Vérifier si la table existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='soumissions_heritage'
                """)
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM soumissions_heritage")
                    count = cursor.fetchone()[0]
                else:
                    count = 0
                conn.close()
                st.metric("Soumissions Heritage", count)
            except Exception as e:
                st.metric("Soumissions Heritage", "0 (Erreur)")
                st.caption(f"Erreur: {str(e)}")
        else:
            st.metric("Soumissions Heritage", "0 (Base non trouvée)")
    
    with col2:
        if os.path.exists('data/soumissions_multi.db'):
            try:
                conn = sqlite3.connect('data/soumissions_multi.db')
                cursor = conn.cursor()
                
                # Vérifier si la table existe
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='soumissions'
                """)
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM soumissions")
                    count = cursor.fetchone()[0]
                else:
                    count = 0
                conn.close()
                st.metric("Soumissions Multi-format", count)
            except Exception as e:
                st.metric("Soumissions Multi-format", "0 (Erreur)")
                st.caption(f"Erreur: {str(e)}")
        else:
            st.metric("Soumissions Multi-format", "0 (Base non trouvée)")

if __name__ == "__main__":
    st.title("🔧 Gestionnaire de sauvegarde")
    show_backup_interface()