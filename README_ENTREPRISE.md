# 🏢 Module de Configuration d'Entreprise

## Vue d'ensemble

Le module de configuration d'entreprise permet de personnaliser complètement les informations de votre entreprise dans l'application de gestion des soumissions. Toutes les soumissions générées utiliseront automatiquement ces informations.

## 🚀 Démarrage rapide

### Accès à la configuration

1. Lancez l'application : `python run.bat` (Windows) ou `./run.sh` (Mac/Linux)
2. Connectez-vous avec le mot de passe admin
3. Cliquez sur l'onglet **🏢 ENTREPRISE** (premier onglet)

### Configuration initiale

Lors de la première utilisation, l'application est configurée avec les informations de Construction Héritage par défaut. Vous pouvez les modifier selon vos besoins.

## 📋 Sections de configuration

### 1. Informations de base
- **Nom de l'entreprise** *(obligatoire)*
- Adresse complète
- Ville
- Province
- Code postal
- Site web

### 2. Coordonnées
- Téléphone bureau
- Téléphone cellulaire
- Courriel principal
- Slogan (optionnel)

### 3. Informations légales
- **Numéro RBQ** (Régie du bâtiment du Québec)
- **Numéro NEQ** (Numéro d'entreprise du Québec)
- **Numéro TPS** (Taxe sur les produits et services)
- **Numéro TVQ** (Taxe de vente du Québec)

### 4. Contact principal
- Nom du contact
- Titre/Poste
- Téléphone direct
- Courriel direct

### 5. Personnalisation visuelle
- **Logo de l'entreprise** (PNG, JPG, GIF, SVG)
  - Format recommandé : PNG transparent
  - Taille maximale recommandée : 500x200px
- **Couleur primaire** : Utilisée pour les en-têtes
- **Couleur secondaire** : Utilisée pour les accents
- **Couleur d'accent** : Utilisée pour les boutons et liens

### 6. Paramètres commerciaux
- **Validité des soumissions** (en jours)
- **Taux d'administration** (%)
- **Taux de contingences** (%)
- **Taux de profit** (%)
- **Modalités de paiement** (texte libre)
- **Garanties offertes** (texte libre)

## 💾 Gestion des configurations

### Sauvegarder
Cliquez sur **💾 Sauvegarder la configuration** pour enregistrer vos modifications.

### Réinitialiser
Cliquez sur **🔄 Réinitialiser aux valeurs par défaut** pour restaurer la configuration initiale.

### Exporter
Cliquez sur **📥 Exporter la configuration** pour télécharger vos paramètres en format JSON.

### Importer
Vous pouvez importer une configuration précédemment exportée via le fichier JSON.

## 🔄 Impact des modifications

Les informations de l'entreprise sont automatiquement utilisées dans :

1. **Soumissions Heritage**
   - En-tête avec logo et informations complètes
   - Pied de page avec coordonnées
   - Numéros d'enregistrement légaux
   - Calculs avec taux personnalisés

2. **Documents uploadés**
   - Liens de validation client
   - Pages d'approbation
   - Exports PDF

3. **Interface utilisateur**
   - Titre de l'application
   - Couleurs de l'interface (si configurées)
   - Informations de contact

## 🧪 Test de la configuration

Pour tester votre configuration :

```bash
python test_entreprise.py
```

Ce script vérifiera :
- Le chargement correct du module
- La sauvegarde et récupération des données
- L'intégration avec les autres modules

## 📁 Structure des données

Les configurations sont stockées dans :
- Base de données : `data/entreprise_config.db`
- Table : `entreprise_config`
- Format : JSON dans un champ TEXT

### Exemple de configuration JSON

```json
{
  "nom": "Ma Construction Inc.",
  "adresse": "123 Rue Example",
  "ville": "Montréal",
  "province": "Québec",
  "code_postal": "H1A 1A1",
  "telephone_bureau": "514-123-4567",
  "telephone_cellulaire": "514-987-6543",
  "email": "info@maconstruction.ca",
  "site_web": "www.maconstruction.ca",
  "rbq": "1234-5678-90",
  "neq": "1234567890",
  "tps": "123456789RT0001",
  "tvq": "1234567890TQ0002",
  "contact_principal_nom": "Jean Dupont",
  "contact_principal_titre": "Président",
  "contact_principal_telephone": "514-123-4567",
  "contact_principal_email": "jean@maconstruction.ca",
  "couleur_primaire": "#1e40af",
  "couleur_secondaire": "#64748b",
  "couleur_accent": "#3b82f6",
  "slogan": "Construire l'avenir ensemble",
  "conditions_paiement": "30% à la signature, 40% au début, 30% à la fin",
  "garanties": "5 ans structure, 2 ans finition",
  "delai_validite_soumission": "30",
  "taux_administration": 5.0,
  "taux_contingences": 10.0,
  "taux_profit": 15.0
}
```

## 🔒 Sécurité

- Les configurations sont stockées localement
- Aucune information sensible n'est transmise en ligne
- Les mots de passe ne sont pas stockés dans cette configuration
- Recommandation : Ne pas inclure d'informations confidentielles dans le slogan

## 🆘 Dépannage

### La configuration ne se sauvegarde pas
1. Vérifiez que le dossier `data/` existe et est accessible en écriture
2. Redémarrez l'application après la sauvegarde

### Le logo ne s'affiche pas
1. Vérifiez le format du fichier (PNG, JPG, GIF, SVG uniquement)
2. Taille maximale : 10 MB
3. Essayez avec une image plus petite

### Les couleurs ne changent pas
1. Les couleurs s'appliquent principalement aux nouvelles soumissions
2. Rafraîchissez la page (F5) après la modification

### Retour aux valeurs par défaut involontaire
1. Exportez régulièrement votre configuration
2. Gardez une copie de sauvegarde du fichier JSON

## 📞 Support

Pour toute question ou problème :
1. Consultez d'abord cette documentation
2. Testez avec le script `test_entreprise.py`
3. Vérifiez les logs dans la console
4. Contactez le support technique si nécessaire

## 🎯 Bonnes pratiques

1. **Complétez tous les champs légaux** pour la conformité
2. **Testez une soumission** après modification
3. **Exportez votre configuration** après chaque modification importante
4. **Utilisez un logo de qualité** pour un rendu professionnel
5. **Harmonisez les couleurs** avec votre charte graphique

---

*Module de Configuration d'Entreprise v1.0 - Compatible avec toutes les versions du système de gestion des soumissions*