# 🔒 Guide de Migration Sécurisée vers Render avec Disque Persistant

## ⚠️ IMPORTANT - SAUVEGARDEZ VOS DONNÉES AVANT LA MIGRATION

Ce guide vous explique comment migrer votre application vers Render **SANS PERDRE vos soumissions existantes**.

---

## 📋 Étape 0 : Sauvegarde des Données Actuelles

### Si vous avez déjà des données sur Render :

1. **Connectez-vous à votre dashboard Render**
2. **Allez dans la console Shell** de votre service
3. **Exécutez ces commandes pour sauvegarder** :

```bash
# Créer une archive de sauvegarde
cd /opt/render/project
tar -czf backup_avant_migration.tar.gz data/

# Afficher le contenu pour vérification
ls -lah backup_avant_migration.tar.gz
```

4. **Téléchargez la sauvegarde** (gardez-la en sécurité)

### Si vous avez des données en local :

```bash
# Windows
python backup_manager.py

# Ou directement
cd data
tar -czf ../backup_local.tar.gz .
```

---

## 🚀 Étape 1 : Configuration du Disque Persistant sur Render

### Option A : Nouveau Service (Recommandé)

1. **Supprimez l'ancien `render.yaml`** et **renommez** `render-disk.yaml` en `render.yaml` :
```bash
mv render.yaml render-old.yaml
mv render-disk.yaml render.yaml
```

2. **Commitez et pushez** vers GitHub :
```bash
git add .
git commit -m "Migration vers disque persistant Render"
git push
```

3. **Sur Render** :
   - Créez un **nouveau Web Service**
   - Connectez votre repo GitHub
   - Render détectera automatiquement le disque persistant
   - **IMPORTANT** : Le disque sera créé automatiquement (1GB gratuit)

### Option B : Service Existant (Plus Risqué)

1. **Dans Render Dashboard** :
   - Allez dans votre service > Settings
   - Section "Disks"
   - Cliquez "Add Disk"
   - Nom : `soumissions-data`
   - Mount Path : `/data`
   - Size : 1 GB

2. **Ajoutez les variables d'environnement** :
   - `DATA_DIR` = `/data/databases`
   - `FILES_DIR` = `/data/files`

3. **Mettez à jour le code** et redéployez

---

## 📦 Étape 2 : Préparation du Code

### Fichiers à vérifier avant le déploiement :

✅ **Nouveaux fichiers créés** :
- `init_render_safe.sh` - Script d'initialisation sécurisé
- `render-disk.yaml` - Configuration avec disque persistant
- `numero_manager.py` - Gestionnaire de numéros unifié
- `fix_duplicates.py` - Correction des doublons
- `MIGRATION_RENDER.md` - Ce guide

✅ **Fichiers modifiés** :
- `Dockerfile` - Supporte le nouveau script
- `app.py` - Utilise numero_manager
- `soumission_heritage.py` - Utilise numero_manager

---

## 🔄 Étape 3 : Migration des Données

### Après le déploiement avec disque persistant :

1. **Vérifiez que le disque est monté** (Console Render) :
```bash
df -h /data
# Devrait montrer le disque de 1GB
```

2. **Si vous aviez des données, restaurez-les** :
```bash
# Uploadez votre backup
# Puis extraire
cd /data
tar -xzf /path/to/backup.tar.gz
```

3. **Vérifiez l'intégrité** :
```bash
python -c "
import sqlite3
for db in ['databases/soumissions_heritage.db', 'databases/soumissions_multi.db']:
    try:
        conn = sqlite3.connect(f'/data/{db}')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM sqlite_master')
        print(f'{db}: OK')
        conn.close()
    except Exception as e:
        print(f'{db}: {e}')
"
```

---

## ✅ Étape 4 : Vérification Post-Migration

### Tests à effectuer :

1. **Connectez-vous à l'application**
2. **Vérifiez que toutes vos soumissions sont présentes**
3. **Créez une nouvelle soumission test**
4. **Redémarrez le service** (Manual Deploy > Deploy)
5. **Vérifiez que la soumission test est toujours là**

Si tout est OK, vos données sont maintenant **persistantes** ! 🎉

---

## 🛡️ Sécurité et Maintenance

### Sauvegardes Automatiques

Le nouveau script `init_render_safe.sh` :
- ✅ Crée une sauvegarde avant chaque démarrage
- ✅ Garde les 5 dernières sauvegardes
- ✅ Vérifie l'intégrité des bases
- ✅ Affiche des statistiques

### Monitoring

Surveillez régulièrement :
```bash
# Espace disque
df -h /data

# Nombre de soumissions
ls -lah /data/databases/

# Logs
tail -f /var/log/render.log
```

---

## 🆘 Troubleshooting

### Problème : "No such file or directory"
**Solution** : Le disque n'est pas monté. Vérifiez la configuration Render.

### Problème : "Database is locked"
**Solution** : Redémarrez le service depuis Render Dashboard.

### Problème : "Permission denied"
**Solution** : 
```bash
chmod -R 777 /data/databases
chmod -R 777 /data/files
```

### Problème : Données perdues après redéploiement
**Solution** : Vous n'utilisez pas le disque persistant. Suivez l'Option A.

---

## 📞 Support

### Avant la migration :
1. **Testez en local** avec `python test_numero_unique.py`
2. **Faites une sauvegarde complète**
3. **Lisez tout ce guide**

### Après la migration :
1. Les données sont dans `/data` (persistant)
2. Les sauvegardes sont dans `/data/backups`
3. Les logs montrent les opérations

---

## 🎯 Checklist Finale

- [ ] Sauvegarde des données existantes effectuée
- [ ] `render-disk.yaml` renommé en `render.yaml`
- [ ] Nouveaux fichiers ajoutés au repo
- [ ] Code pushé sur GitHub
- [ ] Disque persistant configuré sur Render
- [ ] Application déployée avec succès
- [ ] Données vérifiées après déploiement
- [ ] Test de redémarrage effectué
- [ ] Soumissions toujours présentes après redémarrage

---

**💡 CONSEIL** : Si vous n'êtes pas sûr, créez un nouveau service Render pour tester d'abord. Vous pourrez toujours supprimer l'ancien une fois que tout fonctionne.

**🔒 GARANTIE** : Avec le disque persistant, vos données survivront aux redéploiements, redémarrages et mises à jour !

---

*Guide créé pour la migration sécurisée de C2B Construction vers Render avec persistance des données.*