# Protection des Tokens - C2B Heritage

## Vue d'ensemble

Ce système protège automatiquement les tokens de validation client lors des déploiements et mises à jour sur Render.

## Composants du système

### 1. **token_manager.py**
Gestionnaire centralisé des tokens avec les fonctionnalités :
- Sauvegarde automatique de tous les tokens
- Restauration depuis les backups
- Génération de tokens pour les soumissions qui n'en ont pas
- Vérification de l'existence d'un token
- Nettoyage des vieux backups

### 2. **startup.sh**
Script de démarrage principal qui :
1. Sauvegarde les tokens existants
2. Initialise les bases de données si nécessaire
3. Restaure les tokens depuis le dernier backup
4. Génère des tokens pour les nouvelles soumissions
5. Affiche les statistiques
6. Lance l'application

### 3. **init_render.sh**
Script Render avec protection intégrée :
- Sauvegarde avant toute modification
- Restauration après initialisation
- Gestion de l'espace disque

### 4. **fix_client_links.py**
Utilitaire de réparation pour :
- Retrouver les tokens perdus
- Exporter tous les liens clients
- Vérifier l'existence d'un token

## Utilisation

### Commandes disponibles

```bash
# Sauvegarder tous les tokens
python token_manager.py backup

# Restaurer les tokens
python token_manager.py restore

# Générer les tokens manquants
python token_manager.py generate

# Vérifier un token spécifique
python token_manager.py verify <token>

# Afficher les statistiques
python token_manager.py stats

# Nettoyer les vieux backups (garde 30 jours par défaut)
python token_manager.py clean [jours]
```

### Vérifier les liens clients

```bash
# Mode interactif
python fix_client_links.py

# Recherche directe d'un token
python fix_client_links.py <token>

# Vérifier une URL complète
python fix_client_links.py https://c2b-heritage.onrender.com/?token=xxx
```

## Structure des backups

Les backups sont stockés dans :
- Render : `/opt/render/project/data/backups/`
- Local : `data/backups/`

Format des fichiers :
- `tokens_backup_YYYYMMDD_HHMMSS.json` : Backups horodatés
- `tokens_latest.json` : Dernier backup (toujours accessible)

## Protection automatique

### Lors du déploiement
1. Le Dockerfile configure les permissions
2. `startup.sh` est exécuté automatiquement
3. Les tokens sont sauvegardés avant toute modification
4. Les bases sont initialisées si nécessaire
5. Les tokens sont restaurés après initialisation

### Lors des mises à jour
- Les tokens existants sont préservés
- Les nouveaux enregistrements reçoivent automatiquement un token
- Un backup est créé après chaque génération

## Gestion de l'espace disque

Sur Render (disque persistant de 10GB) :
- Nettoyage automatique si utilisation > 80%
- Suppression des backups > 7 jours
- Optimisation des bases SQLite (VACUUM)

## Récupération d'urgence

Si tous les tokens sont perdus :

1. **Chercher dans les backups** :
```bash
ls -la /opt/render/project/data/backups/
```

2. **Restaurer un backup spécifique** :
```bash
python token_manager.py restore /opt/render/project/data/backups/tokens_backup_20250129_120000.json
```

3. **Régénérer les tokens manquants** :
```bash
python token_manager.py generate
```

## Format des tokens

- Format : UUID v4 (ex: `21d66530-0421-49f9-af91-8fd116e3546e`)
- Stockage : Colonne `token` dans les tables SQL
- Unique par soumission
- Généré automatiquement si absent

## Bases de données

### soumissions_heritage.db
- Table : `soumissions_heritage`
- Colonne token : `TEXT UNIQUE`

### soumissions_multi.db
- Table : `soumissions`
- Colonne token : `TEXT UNIQUE NOT NULL`

## Monitoring

Vérifier régulièrement :
```bash
# Statistiques des tokens
python token_manager.py stats

# Espace disque sur Render
df -h /opt/render/project/data

# Nombre de backups
ls -la data/backups/ | wc -l
```

## Troubleshooting

### Tokens non trouvés après déploiement
1. Vérifier les backups : `ls -la data/backups/`
2. Restaurer : `python token_manager.py restore`
3. Régénérer si nécessaire : `python token_manager.py generate`

### Espace disque saturé
1. Nettoyer les backups : `python token_manager.py clean 7`
2. Exécuter : `./clean_disk_render.sh`
3. Supprimer les vieux fichiers uploadés

### Base de données vide
1. Les tokens sont sauvegardés dans `data/backups/`
2. Utiliser `fix_client_links.py` pour diagnostiquer
3. Restaurer avec `token_manager.py restore`

## Sécurité

- Les tokens sont uniques et aléatoires (UUID v4)
- Backups automatiques avant modifications
- Restauration automatique après initialisation
- Multiples copies de sauvegarde conservées