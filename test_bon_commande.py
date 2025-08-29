"""
Script de test pour le système de gestion des bons de commande
Teste les fonctionnalités principales du module bon_commande.py
"""

import os
import sys
import sqlite3
from datetime import datetime

# Ajouter le répertoire du projet au chemin Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bon_commande import (
        init_bon_commande_db,
        generer_numero_bon,
        sauvegarder_bon_commande,
        charger_bon_commande,
        lister_bons_commande,
        supprimer_bon_commande,
        dupliquer_bon_commande,
        generer_html_bon_commande
    )
    print("✅ Module bon_commande importé avec succès")
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)

def test_database_initialization():
    """Test l'initialisation de la base de données"""
    print("\n🔧 Test d'initialisation de la base de données...")
    
    try:
        init_bon_commande_db()
        
        # Vérifier que le fichier de base de données existe
        if os.path.exists('data/bon_commande.db'):
            print("✅ Base de données créée avec succès")
            
            # Vérifier les tables
            conn = sqlite3.connect('data/bon_commande.db')
            cursor = conn.cursor()
            
            # Vérifier la table bons_commande
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bons_commande'")
            if cursor.fetchone():
                print("✅ Table bons_commande créée")
            else:
                print("❌ Table bons_commande manquante")
            
            # Vérifier la table bon_commande_items
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bon_commande_items'")
            if cursor.fetchone():
                print("✅ Table bon_commande_items créée")
            else:
                print("❌ Table bon_commande_items manquante")
            
            # Vérifier la table bon_commande_attachments
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bon_commande_attachments'")
            if cursor.fetchone():
                print("✅ Table bon_commande_attachments créée")
            else:
                print("❌ Table bon_commande_attachments manquante")
            
            conn.close()
        else:
            print("❌ Fichier de base de données non trouvé")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")

def test_numero_generation():
    """Test la génération de numéros de bon"""
    print("\n🔢 Test de génération de numéros...")
    
    try:
        numero1 = generer_numero_bon()
        numero2 = generer_numero_bon()
        
        print(f"✅ Numéro généré 1: {numero1}")
        print(f"✅ Numéro généré 2: {numero2}")
        
        # Vérifier le format
        current_year = datetime.now().year
        if numero1.startswith(f'BC-{current_year}-'):
            print("✅ Format de numéro correct")
        else:
            print("❌ Format de numéro incorrect")
            
    except Exception as e:
        print(f"❌ Erreur lors de la génération : {e}")

def test_bon_commande_operations():
    """Test les opérations CRUD sur les bons de commande"""
    print("\n📋 Test des opérations sur les bons de commande...")
    
    try:
        # Créer un bon de commande de test
        test_data = {
            'numeroBon': 'TEST-2025-001',
            'dateBon': datetime.now().strftime('%Y-%m-%d'),
            'entreprise': {
                'nom': 'Test Entreprise',
                'adresse': '123 Rue Test',
                'ville': 'Test-Ville (Québec) H1H 1H1',
                'tel': '514-123-4567',
                'cell': '438-123-4567',
                'email': 'test@exemple.com',
                'rbq': 'TEST-123',
                'neq': '123456789'
            },
            'fournisseur': {
                'nom': 'Fournisseur Test',
                'adresse': '456 Rue Fournisseur',
                'ville': 'Ville-Fournisseur',
                'codePostal': 'J2J 2J2',
                'tel': '450-987-6543',
                'cell': '514-987-6543',
                'contact': 'Jean Dupont'
            },
            'projet': {
                'nomClient': 'Client Test',
                'nomProjet': 'Projet Test',
                'lieu': 'Lieu Test',
                'refSoumission': 'REF-001',
                'chargeProjet': 'Manager Test'
            },
            'conditions': {
                'validite': '30 jours',
                'paiement': 'Net 30 jours',
                'dateDebut': '2025-01-01',
                'dateFin': '2025-01-31'
            },
            'signatures': {
                'auteur': 'Auteur Test',
                'dateAuteur': '2025-01-01',
                'fournisseur': 'Fournisseur Test',
                'dateFournisseur': '2025-01-02'
            },
            'items': [
                {
                    'id': 1,
                    'number': 1,
                    'title': 'Item Test 1',
                    'description': 'Description de l\'item de test 1',
                    'quantity': 2,
                    'unit': 'unité',
                    'unitPrice': 100.00,
                    'total': 200.00
                },
                {
                    'id': 2,
                    'number': 2,
                    'title': 'Item Test 2',
                    'description': 'Description de l\'item de test 2',
                    'quantity': 1,
                    'unit': 'forfait',
                    'unitPrice': 500.00,
                    'total': 500.00
                }
            ],
            'attachments': []
        }
        
        # Test de sauvegarde
        print("💾 Test de sauvegarde...")
        bon_id = sauvegarder_bon_commande(test_data)
        if bon_id:
            print(f"✅ Bon de commande sauvegardé avec l'ID: {bon_id}")
        else:
            print("❌ Erreur lors de la sauvegarde")
            return
        
        # Test de chargement
        print("📂 Test de chargement...")
        loaded_data = charger_bon_commande('TEST-2025-001')
        if loaded_data:
            print("✅ Bon de commande chargé avec succès")
            print(f"   - Numéro: {loaded_data['numeroBon']}")
            print(f"   - Fournisseur: {loaded_data['fournisseur']['nom']}")
            print(f"   - Nombre d'items: {len(loaded_data['items'])}")
        else:
            print("❌ Erreur lors du chargement")
            return
        
        # Test de listage
        print("📋 Test de listage...")
        bons_list = lister_bons_commande()
        if bons_list:
            print(f"✅ {len(bons_list)} bon(s) de commande trouvé(s)")
            for bon in bons_list:
                print(f"   - {bon.get('numero_bon')} ({bon.get('fournisseur_nom', 'Sans nom')})")
        else:
            print("⚠️ Aucun bon de commande trouvé")
        
        # Test de duplication
        print("📋 Test de duplication...")
        nouveau_numero = dupliquer_bon_commande('TEST-2025-001')
        if nouveau_numero:
            print(f"✅ Bon dupliqué avec le numéro: {nouveau_numero}")
            
            # Vérifier que le nouveau bon existe
            duplicated_data = charger_bon_commande(nouveau_numero)
            if duplicated_data:
                print("✅ Bon dupliqué chargé avec succès")
            else:
                print("❌ Erreur lors du chargement du bon dupliqué")
        else:
            print("❌ Erreur lors de la duplication")
        
        # Test de suppression du bon dupliqué
        if nouveau_numero:
            print("🗑️ Test de suppression du bon dupliqué...")
            if supprimer_bon_commande(nouveau_numero):
                print(f"✅ Bon {nouveau_numero} supprimé avec succès")
            else:
                print(f"❌ Erreur lors de la suppression de {nouveau_numero}")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests CRUD : {e}")
        import traceback
        traceback.print_exc()

def test_html_generation():
    """Test la génération HTML"""
    print("\n🌐 Test de génération HTML...")
    
    try:
        # Vérifier que le fichier template existe
        template_path = 'bon-commande-moderne.html'
        if not os.path.exists(template_path):
            print(f"❌ Template HTML non trouvé: {template_path}")
            return
        
        # Charger un bon existant
        loaded_data = charger_bon_commande('TEST-2025-001')
        if not loaded_data:
            print("❌ Aucun bon de test disponible pour générer le HTML")
            return
        
        # Générer le HTML
        html_content = generer_html_bon_commande(loaded_data)
        if html_content:
            print("✅ HTML généré avec succès")
            print(f"   - Longueur: {len(html_content)} caractères")
            
            # Vérifier quelques éléments clés
            if 'BON DE COMMANDE' in html_content:
                print("✅ Titre du bon présent")
            else:
                print("❌ Titre du bon manquant")
            
            if loaded_data['numeroBon'] in html_content:
                print("✅ Numéro du bon présent")
            else:
                print("❌ Numéro du bon manquant")
            
        else:
            print("❌ Erreur lors de la génération HTML")
            
    except Exception as e:
        print(f"❌ Erreur lors du test HTML : {e}")

def cleanup_test_data():
    """Nettoie les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    
    try:
        # Supprimer le bon de test
        if supprimer_bon_commande('TEST-2025-001'):
            print("✅ Bon de test supprimé")
        else:
            print("⚠️ Bon de test non trouvé ou déjà supprimé")
            
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage : {e}")

def main():
    """Fonction principale des tests"""
    print("🧪 TESTS DU SYSTÈME DE GESTION DES BONS DE COMMANDE")
    print("=" * 60)
    
    # Créer le dossier data s'il n'existe pas
    os.makedirs('data', exist_ok=True)
    
    # Exécuter les tests
    test_database_initialization()
    test_numero_generation()
    test_bon_commande_operations()
    test_html_generation()
    cleanup_test_data()
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")

if __name__ == "__main__":
    main()