"""
Script de test pour le module de configuration d'entreprise
"""

import sys
import os

# Ajouter le chemin au sys.path si nécessaire
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_entreprise_config():
    """Test du module de configuration d'entreprise"""
    print("🔧 Test du module de configuration d'entreprise\n")
    print("=" * 50)
    
    try:
        # Import du module
        from entreprise_config import (
            get_entreprise_config,
            save_entreprise_config,
            get_formatted_company_info,
            get_company_colors,
            get_commercial_params,
            init_entreprise_table
        )
        print("✅ Module importé avec succès")
        
        # Initialiser la base de données
        init_entreprise_table()
        print("✅ Base de données initialisée")
        
        # Récupérer la configuration actuelle
        config = get_entreprise_config()
        print("\n📋 Configuration actuelle:")
        print(f"  - Nom: {config.get('nom')}")
        print(f"  - Adresse: {config.get('adresse')}")
        print(f"  - Ville: {config.get('ville')}")
        print(f"  - Province: {config.get('province')}")
        print(f"  - Téléphone: {config.get('telephone_bureau')}")
        print(f"  - Email: {config.get('email')}")
        print(f"  - RBQ: {config.get('rbq')}")
        print(f"  - NEQ: {config.get('neq')}")
        
        # Tester la récupération des informations formatées
        formatted_info = get_formatted_company_info()
        print("\n📄 Informations formatées:")
        print(f"  - Header: {formatted_info['header']}")
        print(f"  - Adresse complète: {formatted_info['full_address']}")
        
        # Tester les couleurs
        colors = get_company_colors()
        print("\n🎨 Couleurs de l'entreprise:")
        print(f"  - Primaire: {colors['primary']}")
        print(f"  - Secondaire: {colors['secondary']}")
        print(f"  - Accent: {colors['accent']}")
        
        # Tester les paramètres commerciaux
        params = get_commercial_params()
        print("\n💼 Paramètres commerciaux:")
        print(f"  - Taux administration: {params['taux_administration']}%")
        print(f"  - Taux contingences: {params['taux_contingences']}%")
        print(f"  - Taux profit: {params['taux_profit']}%")
        print(f"  - Validité soumission: {params['delai_validite']} jours")
        
        # Test de modification
        print("\n🔄 Test de modification de configuration...")
        test_config = config.copy()
        test_config['nom'] = "Entreprise Test ABC"
        test_config['telephone_bureau'] = "514-555-1234"
        
        success, message = save_entreprise_config(test_config)
        if success:
            print(f"✅ Configuration modifiée: {message}")
            
            # Vérifier la modification
            new_config = get_entreprise_config()
            assert new_config['nom'] == "Entreprise Test ABC"
            assert new_config['telephone_bureau'] == "514-555-1234"
            print("✅ Modifications vérifiées")
            
            # Restaurer la configuration originale
            save_entreprise_config(config)
            print("✅ Configuration originale restaurée")
        else:
            print(f"❌ Erreur lors de la modification: {message}")
        
        print("\n" + "=" * 50)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_integration_soumission():
    """Test de l'intégration avec le module soumission_heritage"""
    print("\n🔧 Test d'intégration avec soumission_heritage\n")
    print("=" * 50)
    
    try:
        # Import du module soumission
        from soumission_heritage import get_company_info
        
        # Récupérer les informations de l'entreprise
        company_info = get_company_info()
        
        print("📋 Informations récupérées dans soumission_heritage:")
        for key, value in company_info.items():
            if value:  # N'afficher que les valeurs non vides
                print(f"  - {key}: {value}")
        
        print("\n✅ Intégration réussie!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test d'intégration: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 DÉMARRAGE DES TESTS DE CONFIGURATION D'ENTREPRISE")
    print("=" * 70)
    
    # Test du module de configuration
    success1 = test_entreprise_config()
    
    # Test de l'intégration
    success2 = test_integration_soumission()
    
    print("\n" + "=" * 70)
    if success1 and success2:
        print("🎉 TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS!")
    else:
        print("⚠️ Certains tests ont échoué. Vérifiez les messages d'erreur ci-dessus.")
    
    print("\n📝 Pour lancer l'application principale, exécutez:")
    print("   python -m streamlit run app.py")

if __name__ == "__main__":
    main()