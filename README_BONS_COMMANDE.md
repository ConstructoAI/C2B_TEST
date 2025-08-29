# 📋 Système de Gestion des Bons de Commande

## Vue d'ensemble

Ce système complet de gestion des bons de commande a été intégré dans l'architecture existante de C2B Construction. Il utilise le template HTML interactif `bon-commande-moderne.html` et s'intègre parfaitement avec l'interface Streamlit existante.

## 🚀 Fonctionnalités

### ✨ Fonctionnalités Principales

- **📝 Création de bons de commande** : Interface HTML interactive complète
- **📋 Gestion centralisée** : Visualisation, modification, duplication et suppression
- **💾 Sauvegarde automatique** : Base de données SQLite intégrée
- **🔄 Numérotation automatique** : Format BC-YYYY-NNN (ex: BC-2025-001)
- **📊 Tableaux de bord** : Statistiques et listes détaillées
- **🏢 Multi-entreprises** : Intégration avec le système de configuration d'entreprise existant

### 🛠️ Fonctionnalités Avancées

- **📎 Pièces jointes** : Support complet des fichiers joints
- **🖊️ Signatures électroniques** : Gestion des signatures et dates
- **💰 Calculs automatiques** : TPS, TVQ, sous-totaux et totaux
- **📤 Export** : Téléchargement HTML complet pour impression
- **🔄 Duplication intelligente** : Copie rapide avec nouveau numéro
- **🔍 Recherche avancée** : Filtres par fournisseur, projet, montant

## 📁 Architecture du Projet

### Fichiers Créés/Modifiés

```
C2B_TEST-main/
├── bon_commande.py              # Module principal de gestion
├── app.py                       # Interface Streamlit modifiée
├── bon-commande-moderne.html    # Template HTML interactif (existant)
├── test_bon_commande.py         # Tests automatisés
└── README_BONS_COMMANDE.md      # Cette documentation
```

### Base de Données

Le système crée automatiquement une base SQLite dans `data/bon_commande.db` avec les tables :

- **bons_commande** : Données principales des bons
- **bon_commande_items** : Items/lignes des bons
- **bon_commande_attachments** : Pièces jointes

## 🔧 Installation et Configuration

### Prérequis

- Python 3.8+
- Streamlit
- SQLite3 (inclus avec Python)
- Modules existants : `entreprise_config.py`, `streamlit_compat.py`

### Démarrage

1. **Lancer l'application Streamlit** :
   ```bash
   streamlit run app.py
   ```

2. **Se connecter en tant qu'administrateur** avec le mot de passe configuré

3. **Accéder à l'onglet "📋 BONS DE COMMANDE"** dans l'interface

## 📖 Guide d'Utilisation

### 1. Créer un Nouveau Bon de Commande

1. Aller dans l'onglet **"📝 Nouveau Bon"**
2. Un numéro unique est automatiquement généré
3. Remplir le formulaire HTML interactif :
   - **Informations Fournisseur** : Nom, adresse, contacts
   - **Informations Projet** : Client, projet, référence soumission
   - **Items** : Ajouter/modifier les lignes du bon
   - **Conditions** : Validité, paiement, dates
   - **Signatures** : Autorisation et acceptation
   - **Pièces jointes** : Drag & drop de fichiers

4. Utiliser les boutons intégrés :
   - **💾 Sauvegarder** : Sauvegarde dans la base
   - **📄 Télécharger HTML** : Export pour impression
   - **🖨️ Imprimer** : Impression directe

### 2. Gestion des Bons Existants

#### Onglet "📋 Gestionnaire"
- **Sélectionner** un bon dans la liste déroulante
- **👁️ Visualiser** : Mode lecture seule
- **✏️ Modifier** : Mode édition interactive
- **📋 Dupliquer** : Créer une copie avec nouveau numéro
- **🗑️ Supprimer** : Suppression avec confirmation

#### Onglet "📊 Liste des Bons"
- **Statistiques** : Total, montants, statuts
- **Recherche** : Filtrer par numéro, fournisseur, projet
- **Vue détaillée** : Informations complètes de chaque bon

### 3. Fonctionnalités Avancées

#### Calculs Automatiques
- **Sous-total** : Somme des items
- **TPS (5%)** : Taxe fédérale
- **TVQ (9.975%)** : Taxe provinciale
- **Total final** : Montant complet

#### Gestion des Pièces Jointes
- **Formats supportés** : PDF, DOC, XLS, images, etc.
- **Taille maximum** : 10 MB par fichier
- **Stockage** : Base64 dans la base de données
- **Visualisation** : Aperçu et téléchargement

#### Export et Impression
- **HTML complet** : Fichier autonome avec CSS intégré
- **Optimisé impression** : Styles spéciaux pour PDF
- **Conservation des couleurs** : Print-friendly

## 🗃️ Structure des Données

### Format JSON Complet

```json
{
  "numeroBon": "BC-2025-001",
  "dateBon": "2025-01-15",
  "entreprise": {
    "nom": "Construction Héritage",
    "adresse": "129 Rue Poirier",
    "ville": "Saint-Jean-sur-Richelieu (Québec) J3B 4E9",
    "tel": "438-524-9193",
    "cell": "514-983-7492",
    "email": "info@constructionheritage.ca",
    "rbq": "5788-9784-01",
    "neq": "1163835623"
  },
  "fournisseur": {
    "nom": "Fournisseur ABC",
    "adresse": "123 Rue Commerce",
    "ville": "Montréal",
    "codePostal": "H1H 1H1",
    "tel": "514-555-0123",
    "cell": "438-555-0123",
    "contact": "Jean Dupont"
  },
  "projet": {
    "nomClient": "Client XYZ",
    "nomProjet": "Rénovation Cuisine",
    "lieu": "Brossard, QC",
    "refSoumission": "S-2025-045",
    "chargeProjet": "Marie Tremblay"
  },
  "conditions": {
    "validite": "30 jours",
    "paiement": "Net 30 jours",
    "dateDebut": "2025-02-01",
    "dateFin": "2025-02-28"
  },
  "items": [
    {
      "id": 1,
      "number": 1,
      "title": "Armoires de cuisine",
      "description": "Armoires en érable, finition naturelle, 12 portes",
      "quantity": 1,
      "unit": "forfait",
      "unitPrice": 3500.00,
      "total": 3500.00
    }
  ],
  "signatures": {
    "auteur": "Pierre Leduc",
    "dateAuteur": "2025-01-15",
    "fournisseur": "",
    "dateFournisseur": ""
  },
  "attachments": [
    {
      "id": "attach_123",
      "name": "devis_details.pdf",
      "size": 245760,
      "type": "application/pdf",
      "data": "base64_encoded_content..."
    }
  ]
}
```

## 🧪 Tests

### Exécuter les Tests Automatisés

```bash
python test_bon_commande.py
```

Les tests couvrent :
- ✅ Initialisation de la base de données
- ✅ Génération de numéros automatique
- ✅ Opérations CRUD complètes
- ✅ Génération HTML
- ✅ Nettoyage automatique

## 🔄 Intégration avec l'Architecture Existante

### Modules Utilisés

- **entreprise_config.py** : Configuration multi-entreprises
- **streamlit_compat.py** : Compatibilité Streamlit
- **backup_manager.py** : Système de sauvegarde global

### Points d'Intégration

1. **Interface Streamlit** : Nouvel onglet "📋 BONS DE COMMANDE"
2. **Base de données** : Séparée mais compatible avec l'existant
3. **Authentification** : Utilise le système admin existant
4. **Configuration** : S'adapte à la configuration d'entreprise

## 🚨 Sécurité et Sauvegarde

### Mesures de Sécurité

- **Authentification** : Accès admin requis
- **Validation des données** : Contrôles de saisie
- **Taille des fichiers** : Limite à 10MB
- **Tokens uniques** : Identification sécurisée

### Sauvegarde

- **Base SQLite** : Fichier `data/bon_commande.db`
- **Pièces jointes** : Encodées en base64
- **Export JSON** : Sauvegarde externe possible
- **Intégration** : Compatible avec `backup_manager.py`

## 📊 Performance et Optimisation

### Optimisations Intégrées

- **Index de base** : Recherche rapide par numéro, date
- **Pagination** : Gestion des grandes listes
- **Cache HTML** : Génération optimisée
- **Requêtes efficaces** : Jointures minimales

### Limites Recommandées

- **Bons actifs** : < 1000 pour performance optimale
- **Pièces jointes** : < 10MB par fichier
- **Items par bon** : < 100 pour interface fluide

## 🛠️ Maintenance et Support

### Logs et Débogage

- **Erreurs SQL** : Affichées dans Streamlit
- **Validation** : Messages d'erreur explicites
- **Debug** : Mode verbose disponible

### Mise à Jour

Pour mettre à jour le système :

1. **Sauvegarder** le dossier `data/`
2. **Remplacer** les fichiers Python modifiés
3. **Redémarrer** l'application Streamlit
4. **Tester** avec `test_bon_commande.py`

## 📞 Support Technique

### Questions Fréquentes

**Q: Le template HTML n'est pas trouvé**
R: Vérifiez que `bon-commande-moderne.html` est dans le dossier racine

**Q: Erreur de base de données**
R: Supprimez `data/bon_commande.db` et relancez (recrée automatiquement)

**Q: Les pièces jointes ne s'affichent pas**
R: Vérifiez la taille des fichiers (< 10MB) et le format

### Contact

- **Développeur** : Sylvain Leduc
- **Projet** : C2B Construction - Système Bons de Commande
- **Version** : 1.0
- **Date** : Janvier 2025

---

## ✨ Fonctionnalités à Venir

- 📧 **Envoi par email** : Expédition automatique aux fournisseurs
- 📱 **Interface mobile** : Version responsive
- 🔗 **API REST** : Intégration externe
- 📈 **Rapports avancés** : Analytics et statistiques
- 🔔 **Notifications** : Alertes de suivi
- 🌐 **Multi-langues** : Support anglais/français

---

*Système créé et intégré avec l'architecture existante de C2B Construction par Claude Code (Anthropic)*