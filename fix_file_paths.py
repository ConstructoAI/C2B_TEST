"""
Script de diagnostic et réparation des chemins de fichiers
Corrige le problème "Fichier non trouvé" sur Render
"""

import sqlite3
import os
import base64
from datetime import datetime

def diagnose_file_paths():
    """Diagnostique les problèmes de chemins de fichiers"""
    print("=" * 60)
    print("DIAGNOSTIC DES CHEMINS DE FICHIERS")
    print("=" * 60)
    
    # Vérifier l'environnement
    print("\n📍 Environnement actuel:")
    print(f"  - Répertoire de travail: {os.getcwd()}")
    print(f"  - Système: {'Render' if os.getenv('RENDER') else 'Local'}")
    
    # Vérifier les dossiers
    print("\n📁 Dossiers de stockage:")
    data_dir = 'data'
    files_dir = 'files'
    
    for dir_name in [data_dir, files_dir]:
        if os.path.exists(dir_name):
            print(f"  ✅ {dir_name}/ existe")
            # Compter les fichiers
            try:
                files = [f for f in os.listdir(dir_name) if os.path.isfile(os.path.join(dir_name, f))]
                print(f"     → {len(files)} fichiers")
            except:
                print(f"     → Erreur de lecture")
        else:
            print(f"  ❌ {dir_name}/ n'existe pas")
    
    # Analyser la base de données
    print("\n📊 Analyse de la base de données:")
    
    if not os.path.exists('data/soumissions_multi.db'):
        print("  ❌ Base de données non trouvée")
        return
    
    conn = sqlite3.connect('data/soumissions_multi.db')
    cursor = conn.cursor()
    
    # Obtenir toutes les soumissions avec file_path
    cursor.execute('''
        SELECT id, numero_soumission, nom_client, file_path, file_data, file_name 
        FROM soumissions 
        WHERE file_path IS NOT NULL OR file_data IS NOT NULL
    ''')
    
    soumissions = cursor.fetchall()
    print(f"  - {len(soumissions)} soumissions avec fichiers")
    
    # Analyser chaque soumission
    problemes = []
    avec_data = 0
    sans_data = 0
    fichiers_ok = 0
    fichiers_manquants = 0
    
    for id_val, numero, client, file_path, file_data, file_name in soumissions:
        has_data = file_data is not None and len(file_data) > 0
        has_path = file_path is not None and file_path != ''
        
        if has_data:
            avec_data += 1
        else:
            sans_data += 1
        
        if has_path:
            if os.path.exists(file_path):
                fichiers_ok += 1
            else:
                fichiers_manquants += 1
                problemes.append({
                    'id': id_val,
                    'numero': numero,
                    'client': client,
                    'file_path': file_path,
                    'file_name': file_name,
                    'has_data': has_data
                })
    
    conn.close()
    
    # Afficher les résultats
    print(f"\n📈 Statistiques:")
    print(f"  - Fichiers avec données BLOB: {avec_data}")
    print(f"  - Fichiers sans données BLOB: {sans_data}")
    print(f"  - Chemins valides: {fichiers_ok}")
    print(f"  - Chemins invalides: {fichiers_manquants}")
    
    if problemes:
        print(f"\n⚠️  {len(problemes)} fichiers introuvables:")
        for p in problemes[:5]:  # Afficher les 5 premiers
            print(f"  - {p['numero']} ({p['client']})")
            print(f"    Chemin: {p['file_path']}")
            print(f"    Données BLOB: {'Oui' if p['has_data'] else 'Non'}")
        
        if len(problemes) > 5:
            print(f"  ... et {len(problemes) - 5} autres")
    
    return problemes

def migrate_to_blob_storage():
    """Migre tous les fichiers vers le stockage BLOB dans la base de données"""
    print("\n" + "=" * 60)
    print("MIGRATION VERS STOCKAGE BLOB")
    print("=" * 60)
    
    if not os.path.exists('data/soumissions_multi.db'):
        print("❌ Base de données non trouvée")
        return
    
    conn = sqlite3.connect('data/soumissions_multi.db')
    cursor = conn.cursor()
    
    # Obtenir les soumissions qui ont un file_path mais pas de file_data
    cursor.execute('''
        SELECT id, numero_soumission, file_path, file_name 
        FROM soumissions 
        WHERE file_path IS NOT NULL 
        AND file_path != ''
        AND (file_data IS NULL OR length(file_data) = 0)
    ''')
    
    soumissions = cursor.fetchall()
    
    if not soumissions:
        print("✅ Aucune migration nécessaire")
        conn.close()
        return
    
    print(f"📋 {len(soumissions)} fichiers à migrer")
    
    migrated = 0
    failed = 0
    
    for id_val, numero, file_path, file_name in soumissions:
        # Essayer de lire le fichier
        if os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                
                # Mettre à jour la base avec les données BLOB
                cursor.execute('''
                    UPDATE soumissions 
                    SET file_data = ?, file_size = ?
                    WHERE id = ?
                ''', (file_data, len(file_data), id_val))
                
                migrated += 1
                print(f"  ✅ {numero} - {file_name} ({len(file_data)/1024:.1f} KB)")
            except Exception as e:
                failed += 1
                print(f"  ❌ {numero} - Erreur: {e}")
        else:
            # Le fichier n'existe pas, essayer de le chercher dans files/
            alt_path = os.path.join('files', os.path.basename(file_path))
            if os.path.exists(alt_path):
                try:
                    with open(alt_path, 'rb') as f:
                        file_data = f.read()
                    
                    cursor.execute('''
                        UPDATE soumissions 
                        SET file_data = ?, file_size = ?, file_path = ?
                        WHERE id = ?
                    ''', (file_data, len(file_data), alt_path, id_val))
                    
                    migrated += 1
                    print(f"  ✅ {numero} - Trouvé dans files/")
                except Exception as e:
                    failed += 1
                    print(f"  ❌ {numero} - Erreur: {e}")
            else:
                failed += 1
                print(f"  ❌ {numero} - Fichier introuvable")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Résultats de la migration:")
    print(f"  - Migrés avec succès: {migrated}")
    print(f"  - Échecs: {failed}")
    
    if migrated > 0:
        print("\n✅ Migration réussie! Les fichiers sont maintenant dans la base de données.")

def test_file_recovery():
    """Teste la récupération des fichiers depuis BLOB"""
    print("\n" + "=" * 60)
    print("TEST DE RÉCUPÉRATION DES FICHIERS")
    print("=" * 60)
    
    if not os.path.exists('data/soumissions_multi.db'):
        print("❌ Base de données non trouvée")
        return
    
    conn = sqlite3.connect('data/soumissions_multi.db')
    cursor = conn.cursor()
    
    # Tester quelques soumissions avec file_data
    cursor.execute('''
        SELECT numero_soumission, file_name, file_data, file_size 
        FROM soumissions 
        WHERE file_data IS NOT NULL 
        AND length(file_data) > 0
        LIMIT 5
    ''')
    
    soumissions = cursor.fetchall()
    conn.close()
    
    if not soumissions:
        print("❌ Aucun fichier BLOB trouvé")
        return
    
    print(f"📋 Test sur {len(soumissions)} fichiers:")
    
    for numero, file_name, file_data, file_size in soumissions:
        actual_size = len(file_data) if file_data else 0
        print(f"\n  {numero} - {file_name}")
        print(f"    Taille déclarée: {file_size/1024:.1f} KB")
        print(f"    Taille réelle: {actual_size/1024:.1f} KB")
        
        if actual_size > 0:
            # Vérifier que c'est bien un fichier valide
            try:
                # Détecter le type MIME
                import magic
                mime = magic.from_buffer(file_data[:1024], mime=True) if len(file_data) > 1024 else "unknown"
                print(f"    Type MIME: {mime}")
                print(f"    ✅ Fichier valide")
            except:
                # Si python-magic n'est pas installé, faire une vérification basique
                if file_data[:4] == b'%PDF':
                    print(f"    Type: PDF")
                elif file_data[:2] == b'PK':
                    print(f"    Type: ZIP/Office")
                else:
                    print(f"    Type: Inconnu")
                print(f"    ✅ Données présentes")
        else:
            print(f"    ❌ Données vides")

def create_test_html():
    """Crée une page HTML de test pour vérifier l'affichage"""
    print("\n" + "=" * 60)
    print("CRÉATION D'UNE PAGE DE TEST")
    print("=" * 60)
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Fichiers</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .file-test { 
                border: 1px solid #ccc; 
                padding: 15px; 
                margin: 10px 0;
                border-radius: 5px;
            }
            .success { background: #d4edda; }
            .error { background: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>Test d'Affichage des Fichiers</h1>
    """
    
    if os.path.exists('data/soumissions_multi.db'):
        conn = sqlite3.connect('data/soumissions_multi.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT numero_soumission, file_name, file_path, file_data 
            FROM soumissions 
            LIMIT 10
        ''')
        
        for numero, file_name, file_path, file_data in cursor.fetchall():
            has_path = file_path and os.path.exists(file_path)
            has_data = file_data and len(file_data) > 0
            
            status = "success" if (has_path or has_data) else "error"
            
            html_content += f"""
            <div class="file-test {status}">
                <h3>{numero} - {file_name}</h3>
                <p>Chemin: {file_path or 'Aucun'}</p>
                <p>Chemin valide: {'✅' if has_path else '❌'}</p>
                <p>Données BLOB: {'✅' if has_data else '❌'}</p>
                <p>Taille: {len(file_data)/1024:.1f if has_data else 0} KB</p>
            </div>
            """
        
        conn.close()
    
    html_content += """
    </body>
    </html>
    """
    
    # Sauvegarder le fichier
    with open('test_files.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Page de test créée: test_files.html")

def main():
    """Menu principal"""
    print("\n🔧 RÉPARATION DES FICHIERS NON TROUVÉS")
    print("=" * 60)
    
    while True:
        print("\nOPTIONS:")
        print("1. Diagnostiquer les problèmes")
        print("2. Migrer vers stockage BLOB (recommandé)")
        print("3. Tester la récupération des fichiers")
        print("4. Créer une page de test HTML")
        print("0. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            diagnose_file_paths()
        elif choice == '2':
            response = input("\n⚠️  Cette opération va stocker tous les fichiers dans la base de données.\nContinuer? (o/n): ")
            if response.lower() in ['o', 'oui', 'y', 'yes']:
                migrate_to_blob_storage()
        elif choice == '3':
            test_file_recovery()
        elif choice == '4':
            create_test_html()

if __name__ == "__main__":
    main()