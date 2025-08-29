"""
Gestionnaire de tokens pour C2B Heritage
Assure la persistance et la protection des tokens
"""

import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import shutil

class TokenManager:
    """Gestionnaire centralisé pour les tokens"""
    
    def __init__(self):
        self.backup_dir = '/opt/render/project/data/backups' if os.getenv('RENDER') else 'data/backups'
        self.data_dir = '/opt/render/project/data' if os.getenv('RENDER') else 'data'
        self.heritage_db = os.path.join(self.data_dir, 'soumissions_heritage.db')
        self.multi_db = os.path.join(self.data_dir, 'soumissions_multi.db')
        
        # Créer les répertoires si nécessaire
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
    
    def backup_all_tokens(self) -> str:
        """Sauvegarde tous les tokens existants"""
        tokens = []
        
        # Collecter les tokens de Heritage
        if os.path.exists(self.heritage_db):
            try:
                conn = sqlite3.connect(self.heritage_db)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT numero, client_nom, token, created_at 
                    FROM soumissions_heritage 
                    WHERE token IS NOT NULL
                ''')
                for row in cursor.fetchall():
                    tokens.append({
                        'numero': row[0],
                        'client': row[1],
                        'token': row[2],
                        'date': row[3],
                        'source': 'heritage'
                    })
                conn.close()
            except Exception as e:
                print(f"Erreur lecture Heritage: {e}")
        
        # Collecter les tokens de Multi
        if os.path.exists(self.multi_db):
            try:
                conn = sqlite3.connect(self.multi_db)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT numero_soumission, nom_client, token, date_creation 
                    FROM soumissions 
                    WHERE token IS NOT NULL
                ''')
                for row in cursor.fetchall():
                    tokens.append({
                        'numero': row[0],
                        'client': row[1],
                        'token': row[2],
                        'date': row[3],
                        'source': 'multi'
                    })
                conn.close()
            except Exception as e:
                print(f"Erreur lecture Multi: {e}")
        
        # Sauvegarder dans un fichier avec timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(self.backup_dir, f'tokens_backup_{timestamp}.json')
        
        backup_data = {
            'date': datetime.now().isoformat(),
            'count': len(tokens),
            'tokens': tokens
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        # Garder une copie toujours accessible
        latest_file = os.path.join(self.data_dir, 'tokens_latest.json')
        with open(latest_file, 'w') as f:
            json.dump(tokens, f)
        
        print(f"✅ {len(tokens)} tokens sauvegardés dans {backup_file}")
        return backup_file
    
    def restore_tokens(self, backup_file: Optional[str] = None) -> int:
        """Restaure les tokens depuis un backup"""
        restored = 0
        
        # Utiliser le dernier backup si aucun fichier spécifié
        if not backup_file:
            latest_file = os.path.join(self.data_dir, 'tokens_latest.json')
            if os.path.exists(latest_file):
                backup_file = latest_file
            else:
                # Chercher le backup le plus récent
                backups = sorted([
                    f for f in os.listdir(self.backup_dir) 
                    if f.startswith('tokens_backup_') and f.endswith('.json')
                ], reverse=True)
                if backups:
                    backup_file = os.path.join(self.backup_dir, backups[0])
        
        if not backup_file or not os.path.exists(backup_file):
            print("❌ Aucun backup trouvé")
            return 0
        
        # Charger les tokens
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        # Si c'est un backup complet, extraire les tokens
        if isinstance(data, dict) and 'tokens' in data:
            tokens = data['tokens']
        else:
            tokens = data
        
        # Restaurer dans Heritage
        if os.path.exists(self.heritage_db):
            try:
                conn = sqlite3.connect(self.heritage_db)
                cursor = conn.cursor()
                
                for item in [t for t in tokens if t['source'] == 'heritage']:
                    # Vérifier si l'enregistrement existe
                    cursor.execute('SELECT token FROM soumissions_heritage WHERE numero = ?', 
                                 (item['numero'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        if not existing[0]:  # Token vide
                            cursor.execute('''
                                UPDATE soumissions_heritage 
                                SET token = ? 
                                WHERE numero = ?
                            ''', (item['token'], item['numero']))
                            if cursor.rowcount > 0:
                                restored += 1
                    else:
                        # Créer l'enregistrement s'il n'existe pas
                        cursor.execute('''
                            INSERT INTO soumissions_heritage 
                            (numero, client_nom, token, created_at) 
                            VALUES (?, ?, ?, ?)
                        ''', (item['numero'], item['client'], item['token'], item['date']))
                        restored += 1
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Erreur restauration Heritage: {e}")
        
        # Restaurer dans Multi
        if os.path.exists(self.multi_db):
            try:
                conn = sqlite3.connect(self.multi_db)
                cursor = conn.cursor()
                
                for item in [t for t in tokens if t['source'] == 'multi']:
                    # Vérifier si l'enregistrement existe
                    cursor.execute('SELECT token FROM soumissions WHERE numero_soumission = ?', 
                                 (item['numero'],))
                    existing = cursor.fetchone()
                    
                    if existing:
                        if not existing[0]:  # Token vide
                            cursor.execute('''
                                UPDATE soumissions 
                                SET token = ? 
                                WHERE numero_soumission = ?
                            ''', (item['token'], item['numero']))
                            if cursor.rowcount > 0:
                                restored += 1
                    else:
                        # Note: On ne crée pas de nouvelles soumissions dans Multi
                        # car elles nécessitent plus de données
                        pass
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Erreur restauration Multi: {e}")
        
        print(f"✅ {restored} tokens restaurés")
        return restored
    
    def generate_missing_tokens(self) -> int:
        """Génère des tokens pour les soumissions qui n'en ont pas"""
        generated = 0
        
        # Générer pour Heritage
        if os.path.exists(self.heritage_db):
            try:
                conn = sqlite3.connect(self.heritage_db)
                cursor = conn.cursor()
                
                # Vérifier si la colonne token existe
                cursor.execute("PRAGMA table_info(soumissions_heritage)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'token' not in columns:
                    cursor.execute('ALTER TABLE soumissions_heritage ADD COLUMN token TEXT UNIQUE')
                    conn.commit()
                
                # Générer des tokens manquants
                cursor.execute('SELECT id FROM soumissions_heritage WHERE token IS NULL')
                for (id_val,) in cursor.fetchall():
                    new_token = str(uuid.uuid4())
                    cursor.execute('''
                        UPDATE soumissions_heritage 
                        SET token = ? 
                        WHERE id = ?
                    ''', (new_token, id_val))
                    generated += 1
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Erreur génération Heritage: {e}")
        
        # Générer pour Multi
        if os.path.exists(self.multi_db):
            try:
                conn = sqlite3.connect(self.multi_db)
                cursor = conn.cursor()
                
                cursor.execute('SELECT id FROM soumissions WHERE token IS NULL')
                for (id_val,) in cursor.fetchall():
                    new_token = str(uuid.uuid4())
                    cursor.execute('''
                        UPDATE soumissions 
                        SET token = ? 
                        WHERE id = ?
                    ''', (new_token, id_val))
                    generated += 1
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Erreur génération Multi: {e}")
        
        if generated > 0:
            print(f"✅ {generated} nouveaux tokens générés")
            # Faire un backup après génération
            self.backup_all_tokens()
        
        return generated
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Vérifie l'existence d'un token et retourne ses informations"""
        # Chercher dans Heritage
        if os.path.exists(self.heritage_db):
            try:
                conn = sqlite3.connect(self.heritage_db)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT numero, client_nom, projet_nom, statut 
                    FROM soumissions_heritage 
                    WHERE token = ?
                ''', (token,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    return {
                        'source': 'heritage',
                        'numero': result[0],
                        'client': result[1],
                        'projet': result[2],
                        'statut': result[3]
                    }
            except:
                pass
        
        # Chercher dans Multi
        if os.path.exists(self.multi_db):
            try:
                conn = sqlite3.connect(self.multi_db)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT numero_soumission, nom_client, nom_projet, statut 
                    FROM soumissions 
                    WHERE token = ?
                ''', (token,))
                result = cursor.fetchone()
                conn.close()
                
                if result:
                    return {
                        'source': 'multi',
                        'numero': result[0],
                        'client': result[1],
                        'projet': result[2],
                        'statut': result[3]
                    }
            except:
                pass
        
        return None
    
    def clean_old_backups(self, keep_days: int = 30) -> int:
        """Nettoie les vieux backups pour économiser l'espace"""
        deleted = 0
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 3600)
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('tokens_backup_') and filename.endswith('.json'):
                filepath = os.path.join(self.backup_dir, filename)
                if os.path.getmtime(filepath) < cutoff_date:
                    os.remove(filepath)
                    deleted += 1
        
        if deleted > 0:
            print(f"🗑️ {deleted} vieux backups supprimés")
        
        return deleted
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur les tokens"""
        stats = {
            'heritage_total': 0,
            'heritage_with_token': 0,
            'multi_total': 0,
            'multi_with_token': 0,
            'backups_count': 0,
            'latest_backup': None
        }
        
        # Stats Heritage
        if os.path.exists(self.heritage_db):
            try:
                conn = sqlite3.connect(self.heritage_db)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM soumissions_heritage')
                stats['heritage_total'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM soumissions_heritage WHERE token IS NOT NULL')
                stats['heritage_with_token'] = cursor.fetchone()[0]
                conn.close()
            except:
                pass
        
        # Stats Multi
        if os.path.exists(self.multi_db):
            try:
                conn = sqlite3.connect(self.multi_db)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM soumissions')
                stats['multi_total'] = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM soumissions WHERE token IS NOT NULL')
                stats['multi_with_token'] = cursor.fetchone()[0]
                conn.close()
            except:
                pass
        
        # Stats backups
        if os.path.exists(self.backup_dir):
            backups = [f for f in os.listdir(self.backup_dir) 
                      if f.startswith('tokens_backup_') and f.endswith('.json')]
            stats['backups_count'] = len(backups)
            if backups:
                latest = sorted(backups, reverse=True)[0]
                stats['latest_backup'] = latest
        
        return stats


def main():
    """Interface ligne de commande"""
    import sys
    
    manager = TokenManager()
    
    if len(sys.argv) < 2:
        print("Usage: python token_manager.py [backup|restore|generate|verify|stats|clean]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'backup':
        backup_file = manager.backup_all_tokens()
        print(f"Backup créé: {backup_file}")
    
    elif command == 'restore':
        backup_file = sys.argv[2] if len(sys.argv) > 2 else None
        restored = manager.restore_tokens(backup_file)
        print(f"{restored} tokens restaurés")
    
    elif command == 'generate':
        generated = manager.generate_missing_tokens()
        print(f"{generated} tokens générés")
    
    elif command == 'verify':
        if len(sys.argv) < 3:
            print("Usage: python token_manager.py verify <token>")
            sys.exit(1)
        token = sys.argv[2]
        info = manager.verify_token(token)
        if info:
            print(f"✅ Token valide: {info}")
        else:
            print(f"❌ Token non trouvé: {token}")
    
    elif command == 'stats':
        stats = manager.get_statistics()
        print("📊 Statistiques des tokens:")
        print(f"  Heritage: {stats['heritage_with_token']}/{stats['heritage_total']}")
        print(f"  Multi: {stats['multi_with_token']}/{stats['multi_total']}")
        print(f"  Backups: {stats['backups_count']}")
        print(f"  Dernier: {stats['latest_backup']}")
    
    elif command == 'clean':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        deleted = manager.clean_old_backups(days)
        print(f"{deleted} backups supprimés")
    
    else:
        print(f"Commande inconnue: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()