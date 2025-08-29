"""
Script pour réparer et vérifier les liens clients avec tokens
Restaure l'accès aux liens de validation client
"""

import sqlite3
import os
import sys
from datetime import datetime

# Configuration
DATABASE_MULTI = 'data/soumissions_multi.db'
DATABASE_HERITAGE = 'data/soumissions_heritage.db'
BASE_URL = 'https://c2b-heritage.onrender.com'  # Modifier selon votre URL

def check_databases():
    """Vérifie l'existence des bases de données"""
    print("=" * 60)
    print("VÉRIFICATION DES BASES DE DONNÉES")
    print("=" * 60)
    
    if os.path.exists(DATABASE_MULTI):
        print(f"✅ Base Multi-format trouvée: {DATABASE_MULTI}")
        size = os.path.getsize(DATABASE_MULTI) / 1024 / 1024
        print(f"   Taille: {size:.2f} MB")
    else:
        print(f"❌ Base Multi-format non trouvée: {DATABASE_MULTI}")
    
    if os.path.exists(DATABASE_HERITAGE):
        print(f"✅ Base Heritage trouvée: {DATABASE_HERITAGE}")
        size = os.path.getsize(DATABASE_HERITAGE) / 1024 / 1024
        print(f"   Taille: {size:.2f} MB")
    else:
        print(f"❌ Base Heritage non trouvée: {DATABASE_HERITAGE}")
    
    print()

def list_all_tokens():
    """Liste tous les tokens existants dans les deux bases"""
    all_tokens = []
    
    # Tokens de la base Multi-format
    if os.path.exists(DATABASE_MULTI):
        try:
            conn = sqlite3.connect(DATABASE_MULTI)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT token, numero_soumission, nom_client, nom_projet, statut, date_creation 
                FROM soumissions 
                WHERE token IS NOT NULL
                ORDER BY date_creation DESC
            ''')
            
            multi_tokens = cursor.fetchall()
            conn.close()
            
            for token, numero, client, projet, statut, date in multi_tokens:
                all_tokens.append({
                    'source': 'Multi-format',
                    'token': token,
                    'numero': numero,
                    'client': client,
                    'projet': projet,
                    'statut': statut,
                    'date': date,
                    'url': f"{BASE_URL}/?token={token}"
                })
            
            print(f"📋 {len(multi_tokens)} soumissions avec tokens dans Multi-format")
        except Exception as e:
            print(f"❌ Erreur lecture Multi-format: {e}")
    
    # Tokens de la base Heritage
    if os.path.exists(DATABASE_HERITAGE):
        try:
            conn = sqlite3.connect(DATABASE_HERITAGE)
            cursor = conn.cursor()
            
            # Vérifier si la colonne token existe
            cursor.execute("PRAGMA table_info(soumissions_heritage)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'token' in columns:
                cursor.execute('''
                    SELECT token, numero, client_nom, projet_nom, statut, created_at 
                    FROM soumissions_heritage 
                    WHERE token IS NOT NULL
                    ORDER BY created_at DESC
                ''')
                
                heritage_tokens = cursor.fetchall()
                
                for token, numero, client, projet, statut, date in heritage_tokens:
                    all_tokens.append({
                        'source': 'Heritage',
                        'token': token,
                        'numero': numero,
                        'client': client,
                        'projet': projet,
                        'statut': statut,
                        'date': date,
                        'url': f"{BASE_URL}/?token={token}"
                    })
                
                print(f"📋 {len(heritage_tokens)} soumissions avec tokens dans Heritage")
            else:
                print("⚠️  La colonne 'token' n'existe pas dans Heritage")
            
            conn.close()
        except Exception as e:
            print(f"❌ Erreur lecture Heritage: {e}")
    
    return all_tokens

def find_token(token_search):
    """Recherche un token spécifique"""
    found = False
    
    # Recherche dans Multi-format
    if os.path.exists(DATABASE_MULTI):
        try:
            conn = sqlite3.connect(DATABASE_MULTI)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM soumissions WHERE token = ?
            ''', (token_search,))
            
            result = cursor.fetchone()
            if result:
                print(f"\n✅ TOKEN TROUVÉ dans Multi-format!")
                print(f"   Numéro: {result[1]}")
                print(f"   Client: {result[2]}")
                print(f"   Projet: {result[5]}")
                print(f"   Statut: {result[14]}")
                print(f"   URL: {BASE_URL}/?token={token_search}")
                found = True
            
            conn.close()
        except Exception as e:
            print(f"❌ Erreur recherche Multi-format: {e}")
    
    # Recherche dans Heritage
    if os.path.exists(DATABASE_HERITAGE):
        try:
            conn = sqlite3.connect(DATABASE_HERITAGE)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM soumissions_heritage WHERE token = ?
            ''', (token_search,))
            
            result = cursor.fetchone()
            if result:
                print(f"\n✅ TOKEN TROUVÉ dans Heritage!")
                columns = ['id', 'numero', 'client_nom', 'projet_nom', 'montant_total', 
                          'statut', 'token', 'data', 'created_at', 'updated_at', 'lien_public']
                data = dict(zip(columns, result))
                print(f"   Numéro: {data.get('numero')}")
                print(f"   Client: {data.get('client_nom')}")
                print(f"   Projet: {data.get('projet_nom')}")
                print(f"   Statut: {data.get('statut')}")
                print(f"   URL: {BASE_URL}/?token={token_search}")
                found = True
            
            conn.close()
        except Exception as e:
            print(f"❌ Erreur recherche Heritage: {e}")
    
    if not found:
        print(f"\n❌ Token '{token_search}' non trouvé dans aucune base")
    
    return found

def export_all_links():
    """Exporte tous les liens clients dans un fichier"""
    tokens = list_all_tokens()
    
    if not tokens:
        print("\n❌ Aucun token trouvé")
        return
    
    filename = f"liens_clients_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("LISTE DES LIENS CLIENTS\n")
        f.write(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Grouper par statut
        for statut in ['en_attente', 'approuvee', 'refusee', None]:
            tokens_statut = [t for t in tokens if t['statut'] == statut]
            
            if tokens_statut:
                statut_label = statut or 'Sans statut'
                f.write(f"\n{statut_label.upper()} ({len(tokens_statut)} soumissions)\n")
                f.write("-" * 80 + "\n")
                
                for token in tokens_statut:
                    f.write(f"\nNuméro: {token['numero']}\n")
                    f.write(f"Client: {token['client']}\n")
                    f.write(f"Projet: {token['projet']}\n")
                    f.write(f"Date: {token['date']}\n")
                    f.write(f"Source: {token['source']}\n")
                    f.write(f"Lien: {token['url']}\n")
                    f.write("-" * 40 + "\n")
    
    print(f"\n✅ Liens exportés dans: {filename}")
    print(f"   Total: {len(tokens)} liens")

def check_token_from_url(url):
    """Extrait et vérifie un token depuis une URL"""
    if '?token=' in url:
        token = url.split('?token=')[1].split('&')[0]
        print(f"\n🔍 Recherche du token: {token}")
        return find_token(token)
    else:
        print("\n❌ URL invalide - format attendu: ...?token=xxx-xxx-xxx")
        return False

def repair_missing_tokens():
    """Ajoute la colonne token si elle manque et génère des tokens"""
    import uuid
    repairs = 0
    
    # Réparer Heritage
    if os.path.exists(DATABASE_HERITAGE):
        try:
            conn = sqlite3.connect(DATABASE_HERITAGE)
            cursor = conn.cursor()
            
            # Vérifier si la colonne token existe
            cursor.execute("PRAGMA table_info(soumissions_heritage)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'token' not in columns:
                print("\n🔧 Ajout de la colonne 'token' dans Heritage...")
                cursor.execute('ALTER TABLE soumissions_heritage ADD COLUMN token TEXT UNIQUE')
                conn.commit()
            
            # Générer des tokens pour les soumissions qui n'en ont pas
            cursor.execute('SELECT id FROM soumissions_heritage WHERE token IS NULL')
            missing = cursor.fetchall()
            
            for (id_val,) in missing:
                new_token = str(uuid.uuid4())
                cursor.execute('UPDATE soumissions_heritage SET token = ? WHERE id = ?', 
                             (new_token, id_val))
                repairs += 1
            
            if repairs > 0:
                conn.commit()
                print(f"✅ {repairs} tokens générés pour Heritage")
            
            conn.close()
        except Exception as e:
            print(f"❌ Erreur réparation Heritage: {e}")
    
    # Réparer Multi-format
    if os.path.exists(DATABASE_MULTI):
        try:
            conn = sqlite3.connect(DATABASE_MULTI)
            cursor = conn.cursor()
            
            # Générer des tokens pour les soumissions qui n'en ont pas
            cursor.execute('SELECT id FROM soumissions WHERE token IS NULL')
            missing = cursor.fetchall()
            
            for (id_val,) in missing:
                new_token = str(uuid.uuid4())
                cursor.execute('UPDATE soumissions SET token = ? WHERE id = ?', 
                             (new_token, id_val))
                repairs += 1
            
            if len(missing) > 0:
                conn.commit()
                print(f"✅ {len(missing)} tokens générés pour Multi-format")
            
            conn.close()
        except Exception as e:
            print(f"❌ Erreur réparation Multi-format: {e}")
    
    return repairs

def main():
    """Fonction principale"""
    print("\n🔧 UTILITAIRE DE RÉPARATION DES LIENS CLIENTS")
    print("=" * 60)
    
    # Vérifier les bases
    check_databases()
    
    # Menu interactif
    while True:
        print("\n" + "=" * 60)
        print("OPTIONS DISPONIBLES:")
        print("=" * 60)
        print("1. Lister TOUS les liens clients")
        print("2. Rechercher un token spécifique")
        print("3. Vérifier une URL complète")
        print("4. Exporter tous les liens dans un fichier")
        print("5. Réparer les tokens manquants")
        print("6. Afficher les statistiques")
        print("0. Quitter")
        
        choice = input("\nVotre choix (0-6): ").strip()
        
        if choice == '0':
            break
        
        elif choice == '1':
            print("\n📋 LISTE DE TOUS LES LIENS CLIENTS")
            print("-" * 60)
            tokens = list_all_tokens()
            
            if tokens:
                print(f"\nTotal: {len(tokens)} liens trouvés\n")
                
                # Afficher les 10 derniers
                print("Les 10 derniers liens créés:")
                print("-" * 60)
                for token in tokens[:10]:
                    print(f"\n{token['numero']} - {token['client']}")
                    print(f"  Projet: {token['projet']}")
                    print(f"  Statut: {token['statut']}")
                    print(f"  URL: {token['url']}")
                
                if len(tokens) > 10:
                    print(f"\n... et {len(tokens) - 10} autres")
        
        elif choice == '2':
            token = input("\nEntrez le token à rechercher: ").strip()
            if token:
                find_token(token)
        
        elif choice == '3':
            url = input("\nCollez l'URL complète: ").strip()
            if url:
                check_token_from_url(url)
        
        elif choice == '4':
            export_all_links()
        
        elif choice == '5':
            print("\n🔧 Réparation des tokens manquants...")
            repairs = repair_missing_tokens()
            if repairs > 0:
                print(f"\n✅ {repairs} tokens réparés au total")
            else:
                print("\n✅ Aucune réparation nécessaire")
        
        elif choice == '6':
            print("\n📊 STATISTIQUES")
            print("-" * 60)
            tokens = list_all_tokens()
            
            if tokens:
                # Par source
                multi = len([t for t in tokens if t['source'] == 'Multi-format'])
                heritage = len([t for t in tokens if t['source'] == 'Heritage'])
                
                print(f"Par source:")
                print(f"  - Multi-format: {multi}")
                print(f"  - Heritage: {heritage}")
                
                # Par statut
                print(f"\nPar statut:")
                for statut in ['en_attente', 'approuvee', 'refusee', None]:
                    count = len([t for t in tokens if t['statut'] == statut])
                    if count > 0:
                        statut_label = statut or 'Sans statut'
                        print(f"  - {statut_label}: {count}")
                
                print(f"\nTotal: {len(tokens)} soumissions avec liens")

if __name__ == "__main__":
    # Si un argument est passé, recherche directe
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        print(f"\n🔍 Recherche directe: {arg}")
        
        if arg.startswith('http'):
            check_token_from_url(arg)
        else:
            find_token(arg)
    else:
        # Mode interactif
        main()