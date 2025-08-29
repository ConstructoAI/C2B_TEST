"""
Script de test pour vérifier le système de numérotation unique
"""

import sys
import os
import sqlite3
from datetime import datetime

# Ajouter le chemin au sys.path si nécessaire
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_numero_generation():
    """Test la génération de numéros uniques"""
    print("=" * 60)
    print("TEST DU SYSTÈME DE NUMÉROTATION UNIQUE")
    print("=" * 60)
    
    # Test 1: Importer les modules
    print("\n[TEST 1] Import des modules...")
    try:
        from numero_manager import get_safe_unique_number, verify_number_uniqueness
        print("✅ Module numero_manager importé")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    try:
        import app
        print("✅ Module app importé")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    try:
        import soumission_heritage
        print("✅ Module soumission_heritage importé")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Test 2: Génération depuis app.py
    print("\n[TEST 2] Génération depuis app.py...")
    try:
        numero_app = app.get_next_submission_number()
        print(f"✅ Numéro généré: {numero_app}")
        
        # Vérifier l'unicité
        is_unique = verify_number_uniqueness(numero_app)
        if is_unique:
            print(f"✅ Le numéro {numero_app} est unique")
        else:
            print(f"❌ Le numéro {numero_app} existe déjà!")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 3: Génération depuis soumission_heritage.py
    print("\n[TEST 3] Génération depuis soumission_heritage.py...")
    try:
        numero_heritage = soumission_heritage.generate_numero_soumission()
        print(f"✅ Numéro généré: {numero_heritage}")
        
        # Vérifier l'unicité
        is_unique = verify_number_uniqueness(numero_heritage)
        if is_unique:
            print(f"✅ Le numéro {numero_heritage} est unique")
        else:
            print(f"❌ Le numéro {numero_heritage} existe déjà!")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 4: Vérifier que les numéros sont différents
    print("\n[TEST 4] Vérification de l'incrémentation...")
    if numero_app != numero_heritage:
        print(f"✅ Les numéros sont différents: {numero_app} != {numero_heritage}")
    else:
        print(f"❌ Les numéros sont identiques: {numero_app}")
        return False
    
    # Test 5: Génération directe depuis numero_manager
    print("\n[TEST 5] Génération directe depuis numero_manager...")
    try:
        numero_direct = get_safe_unique_number()
        print(f"✅ Numéro généré: {numero_direct}")
        
        if numero_direct not in [numero_app, numero_heritage]:
            print(f"✅ Le numéro est différent des précédents")
        else:
            print(f"❌ Le numéro est identique à un précédent")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 6: Simulation de création simultanée
    print("\n[TEST 6] Simulation de créations simultanées...")
    numeros_generes = []
    
    for i in range(5):
        try:
            # Alterner entre les deux méthodes
            if i % 2 == 0:
                num = app.get_next_submission_number()
                source = "app.py"
            else:
                num = soumission_heritage.generate_numero_soumission()
                source = "heritage"
            
            if num in numeros_generes:
                print(f"❌ Doublon détecté: {num} (depuis {source})")
                return False
            
            numeros_generes.append(num)
            print(f"  ✅ {source}: {num}")
        except Exception as e:
            print(f"❌ Erreur lors de la génération {i+1}: {e}")
            return False
    
    print(f"\n✅ {len(numeros_generes)} numéros uniques générés sans conflit")
    
    return True

def check_existing_duplicates():
    """Vérifie s'il existe des doublons dans les bases actuelles"""
    print("\n" + "=" * 60)
    print("VÉRIFICATION DES DOUBLONS EXISTANTS")
    print("=" * 60)
    
    all_numbers = []
    
    # Vérifier dans Heritage
    try:
        if os.path.exists('data/soumissions_heritage.db'):
            conn = sqlite3.connect('data/soumissions_heritage.db')
            cursor = conn.cursor()
            cursor.execute('SELECT numero FROM soumissions_heritage')
            for row in cursor.fetchall():
                all_numbers.append(('Heritage', row[0]))
            conn.close()
    except:
        pass
    
    # Vérifier dans Multi
    try:
        if os.path.exists('data/soumissions_multi.db'):
            conn = sqlite3.connect('data/soumissions_multi.db')
            cursor = conn.cursor()
            cursor.execute('SELECT numero_soumission FROM soumissions')
            for row in cursor.fetchall():
                all_numbers.append(('Multi', row[0]))
            conn.close()
    except:
        pass
    
    # Analyser
    seen = set()
    duplicates = []
    
    for source, numero in all_numbers:
        if numero in seen:
            duplicates.append(numero)
        seen.add(numero)
    
    if duplicates:
        print(f"\n⚠️  {len(set(duplicates))} numéros en double trouvés:")
        for num in set(duplicates):
            count = sum(1 for s, n in all_numbers if n == num)
            print(f"  - {num} (apparaît {count} fois)")
        print("\n💡 Exécutez 'python fix_duplicates.py' pour corriger")
        return False
    else:
        print("\n✅ Aucun doublon trouvé dans les bases existantes")
        return True

def main():
    """Fonction principale"""
    print("\n🔬 TEST COMPLET DU SYSTÈME DE NUMÉROTATION UNIQUE")
    print("=" * 60)
    
    # Vérifier les doublons existants
    has_no_duplicates = check_existing_duplicates()
    
    # Tester la génération
    test_passed = test_numero_generation()
    
    # Résultats
    print("\n" + "=" * 60)
    print("RÉSULTATS DES TESTS")
    print("=" * 60)
    
    if test_passed and has_no_duplicates:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
        print("\nLe système de numérotation unique fonctionne correctement.")
        print("Les deux modules utilisent maintenant la même source de numérotation.")
    elif test_passed and not has_no_duplicates:
        print("\n⚠️  Les tests de génération sont OK mais des doublons existent.")
        print("Exécutez 'python fix_duplicates.py' pour nettoyer les données.")
    else:
        print("\n❌ Des erreurs ont été détectées.")
        print("Vérifiez les messages d'erreur ci-dessus.")
    
    # Informations supplémentaires
    print("\n" + "=" * 60)
    print("INFORMATIONS SYSTÈME")
    print("=" * 60)
    
    print(f"Date/Heure: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dossier de travail: {os.getcwd()}")
    
    if os.path.exists('data'):
        files = os.listdir('data')
        print(f"Fichiers dans data/: {', '.join(files)}")
    else:
        print("Le dossier data/ n'existe pas")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n\nAppuyez sur Entrée pour fermer...")