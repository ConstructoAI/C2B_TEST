# 🏗️ Gestionnaire de Soumissions C2B Construction

Application web professionnelle pour gérer les soumissions de construction avec module Heritage intégré.

## 🚀 Démarrage Rapide

### Installation Locale
```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

Accès : http://localhost:8501

### Déploiement sur Render

1. Push ce dossier sur GitHub
2. Connectez-vous à [Render](https://render.com)
3. Créez un nouveau Web Service
4. Connectez votre repo GitHub
5. Render détectera automatiquement la configuration

## 📁 Structure

```
├── app.py                 # Application principale
├── soumission_heritage.py # Module Heritage
├── streamlit_compat.py    # Compatibilité Streamlit
├── pdf_viewer.py          # Visualiseur PDF
├── requirements.txt       # Dépendances
├── Dockerfile            # Configuration Docker
├── render.yaml           # Config Render
├── .streamlit/           # Config Streamlit
│   └── config.toml
├── data/                 # Base de données (créé automatiquement)
└── files/                # Fichiers uploadés (créé automatiquement)
```

## 🔑 Accès Admin

**Mot de passe par défaut** : `admin2025`

⚠️ **Important** : Changez le mot de passe dans `app.py` ligne ~64 :
```python
ADMIN_PASSWORD = "VotreNouveauMotDePasse"
```

## ✨ Fonctionnalités

- 📊 **Dashboard** : Vue d'ensemble des soumissions
- ➕ **Créer Soumission** : Module Heritage complet
- 📤 **Upload** : Support PDF, Word, Excel, Images
- 🔗 **Liens Clients** : Approbation en ligne
- ✏️ **Modification** : Éditer les soumissions Heritage
- 🗑️ **Suppression** : Avec confirmation

## 📧 Support

Pour toute question, contactez l'équipe de développement.

---
**C2B Construction © 2024**