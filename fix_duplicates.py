"""
Script pour corriger les numéros de soumission en double
À exécuter une seule fois pour nettoyer les données existantes
"""

import sys
import os

# Ajouter le chemin au sys.path si nécessaire
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from numero_manager import fix_duplicate_numbers, get_safe_unique_number, verify_number_uniqueness
import sqlite3

def analyze_duplicates():
    """Analyse et affiche les doublons existants"""
    print("=" * 60)
    print("ANALYSE DES NUMÉROS DE SOUMISSION EN DOUBLE")
    print("=" * 60)
    
    all_numbers = {}
    duplicates = []
    
    # Analyser soumissions_heritage.db
    print("\n📁 Analyse de soumissions_heritage.db...")
    try:
        if os.path.exists('data/soumissions_heritage.db'):
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, numero, client_nom, created_at FROM soumissions_heritage ORDER BY created_at')
            heritage_data = cursor.fetchall()
            conn.close()
            
            print(f"  - {len(heritage_data)} soumissions trouvées")
            
            for id_val, numero, client, date_creation in heritage_data:
                if numero in all_numbers:
                    duplicates.append({
                        'numero': numero,
                        'source1': all_numbers[numero],
                        'source2': f'Heritage ID:{id_val} - {client} ({date_creation})'
                    })
                else:
                    all_numbers[numero] = f'Heritage ID:{id_val} - {client} ({date_creation})'
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    # Analyser soumissions_multi.db
    print("\n📁 Analyse de soumissions_multi.db...")
    try:
        if os.path.exists('data/soumissions_multi.db'):
            conn = sqlite3.connect('data/soumissions_multi.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, numero_soumission, nom_client, date_creation FROM soumissions ORDER BY date_creation')
            multi_data = cursor.fetchall()
            conn.close()
            
            print(f"  - {len(multi_data)} soumissions trouvées")
            
            for id_val, numero, client, date_creation in multi_data:
                if numero in all_numbers:
                    duplicates.append({
                        'numero': numero,
                        'source1': all_numbers[numero],
                        'source2': f'Multi ID:{id_val} - {client} ({date_creation})'
                    })
                else:
                    all_numbers[numero] = f'Multi ID:{id_val} - {client} ({date_creation})'
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
    
    # Afficher les résultats
    print("\n" + "=" * 60)
    print("RÉSULTATS DE L'ANALYSE")
    print("=" * 60)
    
    if duplicates:
        print(f"\n⚠️  {len(duplicates)} DOUBLONS DÉTECTÉS:")
        print("-" * 60)
        for dup in duplicates:
            print(f"\n📋 Numéro: {dup['numero']}")
            print(f"   Source 1: {dup['source1']}")
            print(f"   Source 2: {dup['source2']}")
    else:
        print("\n✅ Aucun doublon détecté!")
    
    print(f"\n📊 Total des numéros uniques: {len(all_numbers)}")
    
    return len(duplicates)

def main():
    """Fonction principale"""
    print("\n🔧 UTILITAIRE DE CORRECTION DES NUMÉROS EN DOUBLE")
    print("=" * 60)
    
    # Étape 1: Analyser
    print("\n[1/3] Analyse des doublons...")
    duplicate_count = analyze_duplicates()
    
    if duplicate_count == 0:
        print("\n✅ Aucune correction nécessaire!")
        return
    
    # Étape 2: Demander confirmation
    print("\n" + "=" * 60)
    print("⚠️  ATTENTION")
    print("=" * 60)
    print(f"Cette opération va modifier {duplicate_count} soumission(s)")
    print("Les numéros en double seront remplacés par de nouveaux numéros uniques.")
    print("\n⚠️  RECOMMANDATION: Faites une sauvegarde avant de continuer!")
    
    response = input("\nVoulez-vous corriger les doublons? (oui/non): ").lower().strip()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Correction annulée.")
        return
    
    # Étape 3: Corriger
    print("\n[2/3] Correction des doublons...")
    corrections = fix_duplicate_numbers()
    
    if corrections > 0:
        print(f"\n✅ {corrections} doublons corrigés avec succès!")
    else:
        print("\n✅ Aucune correction effectuée.")
    
    # Étape 4: Vérifier
    print("\n[3/3] Vérification finale...")
    duplicate_count_after = analyze_duplicates()
    
    if duplicate_count_after == 0:
        print("\n🎉 SUCCÈS: Tous les doublons ont été corrigés!")
    else:
        print(f"\n⚠️  {duplicate_count_after} doublons restants. Relancez le script si nécessaire.")
    
    # Test du nouveau système
    print("\n" + "=" * 60)
    print("TEST DU NOUVEAU SYSTÈME")
    print("=" * 60)
    
    next_number = get_safe_unique_number()
    print(f"\n📋 Prochain numéro disponible: {next_number}")
    
    is_unique = verify_number_uniqueness(next_number)
    print(f"✅ Unicité vérifiée: {is_unique}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
    except Exception as e:
        print(f"\n\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n\nAppuyez sur Entrée pour fermer...")