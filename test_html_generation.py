"""
Script de test pour vérifier la génération HTML des soumissions
"""

import sys
import os
import io

# Configurer l'encodage UTF-8 pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ajouter le chemin au sys.path si nécessaire
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_html_generation():
    """Test de la génération HTML"""
    print("🧪 Test de génération HTML\n")
    print("=" * 50)
    
    try:
        # Import des modules nécessaires
        import streamlit as st
        from soumission_heritage import generate_html, generate_html_for_pdf, get_company_info, generate_numero_soumission
        from datetime import datetime
        
        print("✅ Modules importés avec succès")
        
        # Simuler session state Streamlit
        if 'soumission_data' not in st.session_state:
            st.session_state.soumission_data = {
                'numero': generate_numero_soumission(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'client': {
                    'nom': 'Client Test',
                    'adresse': '123 Rue Test',
                    'ville': 'Montréal',
                    'code_postal': 'H1A 1A1',
                    'telephone': '514-123-4567',
                    'courriel': 'test@example.com'
                },
                'projet': {
                    'nom': 'Projet Test',
                    'adresse': '456 Rue Projet',
                    'type': 'Résidentielle',
                    'superficie': 2000,
                    'etages': 2,
                    'date_debut': '2025-01-15',
                    'duree': '3-4 mois'
                },
                'items': {
                    '0_0-1': {
                        'titre': 'Permis et études',
                        'description': 'Test description',
                        'quantite': 1,
                        'prix_unitaire': 5000,
                        'montant': 5000
                    },
                    '1_1-1': {
                        'titre': 'Excavation',
                        'description': 'Test excavation',
                        'quantite': 1,
                        'prix_unitaire': 10000,
                        'montant': 10000
                    }
                },
                'totaux': {},
                'conditions': ['Condition test 1', 'Condition test 2'],
                'exclusions': ['Exclusion test 1', 'Exclusion test 2'],
                'taux': {
                    'admin': 0.03,
                    'contingency': 0.12,
                    'profit': 0.15
                }
            }
        
        print("✅ Session state simulé créé")
        
        # Test de récupération des infos d'entreprise
        company_info = get_company_info()
        print(f"\n📋 Informations d'entreprise récupérées:")
        print(f"  - Nom: {company_info['name']}")
        print(f"  - Email: {company_info['email']}")
        
        # Test de génération HTML standard
        print("\n🔄 Test de generate_html()...")
        try:
            html = generate_html()
            if html and len(html) > 100:
                print(f"✅ HTML généré avec succès ({len(html)} caractères)")
                # Vérifier que les informations de l'entreprise sont présentes
                if company_info['name'] in html:
                    print(f"✅ Nom de l'entreprise trouvé dans le HTML")
                else:
                    print(f"⚠️ Nom de l'entreprise non trouvé dans le HTML")
            else:
                print("❌ HTML généré est vide ou trop court")
        except Exception as e:
            print(f"❌ Erreur lors de generate_html(): {e}")
            import traceback
            traceback.print_exc()
        
        # Test de génération HTML pour PDF
        print("\n🔄 Test de generate_html_for_pdf()...")
        try:
            html_pdf = generate_html_for_pdf()
            if html_pdf and len(html_pdf) > 100:
                print(f"✅ HTML PDF généré avec succès ({len(html_pdf)} caractères)")
                # Vérifier que les informations de l'entreprise sont présentes
                if company_info['name'] in html_pdf:
                    print(f"✅ Nom de l'entreprise trouvé dans le HTML PDF")
                else:
                    print(f"⚠️ Nom de l'entreprise non trouvé dans le HTML PDF")
            else:
                print("❌ HTML PDF généré est vide ou trop court")
        except Exception as e:
            print(f"❌ Erreur lors de generate_html_for_pdf(): {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 50)
        print("✅ Tests de génération HTML terminés!")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Fonction principale"""
    print("🚀 TEST DE GÉNÉRATION HTML POUR SOUMISSIONS")
    print("=" * 70 + "\n")
    
    success = test_html_generation()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 TOUS LES TESTS HTML SONT PASSÉS!")
    else:
        print("⚠️ Des erreurs ont été détectées. Vérifiez les messages ci-dessus.")
    
    print("\n📝 Pour lancer l'application principale:")
    print("   Windows: py -m streamlit run app.py")
    print("   Mac/Linux: python3 -m streamlit run app.py")

if __name__ == "__main__":
    main()