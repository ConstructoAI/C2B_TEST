#!/bin/bash

# Script de nettoyage pour libérer de l'espace sur Render
# À exécuter dans la console Shell de Render

echo "=========================================="
echo "🧹 Nettoyage du Disque Persistant Render"
echo "=========================================="
echo ""

# Afficher l'utilisation actuelle
echo "📊 Utilisation actuelle:"
df -h /opt/render/project/data
echo ""

# Analyser l'utilisation par dossier
echo "📁 Répartition de l'espace:"
du -sh /opt/render/project/data/* 2>/dev/null | sort -rh | head -20
echo ""

# Nettoyer les vieux backups
echo "🗑️ Nettoyage des backups..."
BACKUP_DIR="/opt/render/project/data/backups"
if [ -d "$BACKUP_DIR" ]; then
    echo "Backups actuels:"
    ls -lah $BACKUP_DIR/*.tar.gz 2>/dev/null | tail -10
    
    # Supprimer les backups de plus de 7 jours
    find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete 2>/dev/null
    echo "✅ Backups de plus de 7 jours supprimés"
    
    # Garder seulement les 5 derniers backups
    cd $BACKUP_DIR 2>/dev/null
    ls -t backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs rm -f 2>/dev/null
    echo "✅ Gardé seulement les 5 derniers backups"
fi
echo ""

# Nettoyer les fichiers temporaires
echo "🗑️ Nettoyage des fichiers temporaires..."
find /opt/render/project/data -name "*.tmp" -delete 2>/dev/null
find /opt/render/project/data -name "*.log" -mtime +30 -delete 2>/dev/null
find /opt/render/project/data -name ".~lock.*" -delete 2>/dev/null
echo "✅ Fichiers temporaires supprimés"
echo ""

# Analyser les gros fichiers
echo "📊 Les 10 plus gros fichiers:"
find /opt/render/project/data -type f -exec ls -lh {} \; 2>/dev/null | sort -k5 -rh | head -10
echo ""

# Compacter les bases de données SQLite
echo "🗃️ Optimisation des bases de données..."
for db in /opt/render/project/data/*.db; do
    if [ -f "$db" ]; then
        SIZE_BEFORE=$(du -h "$db" | cut -f1)
        sqlite3 "$db" "VACUUM;" 2>/dev/null
        sqlite3 "$db" "ANALYZE;" 2>/dev/null
        SIZE_AFTER=$(du -h "$db" | cut -f1)
        echo "  - $(basename $db): $SIZE_BEFORE -> $SIZE_AFTER"
    fi
done
echo "✅ Bases de données optimisées"
echo ""

# Analyser les fichiers uploadés
echo "📤 Fichiers uploadés (files/):"
FILES_DIR="/opt/render/project/data/files"
if [ -d "$FILES_DIR" ]; then
    FILE_COUNT=$(find $FILES_DIR -type f | wc -l)
    FILE_SIZE=$(du -sh $FILES_DIR | cut -f1)
    echo "  - Nombre de fichiers: $FILE_COUNT"
    echo "  - Espace total: $FILE_SIZE"
    
    # Lister les plus gros fichiers uploadés
    echo "  - Top 5 des plus gros fichiers:"
    find $FILES_DIR -type f -exec ls -lh {} \; | sort -k5 -rh | head -5
fi
echo ""

# Résultat final
echo "=========================================="
echo "✅ Nettoyage terminé!"
echo "=========================================="
echo ""
echo "📊 Utilisation après nettoyage:"
df -h /opt/render/project/data
echo ""

# Calculer l'espace libéré
USAGE_AFTER=$(df /opt/render/project/data | tail -1 | awk '{print $5}' | sed 's/%//')
echo "💾 Espace utilisé: ${USAGE_AFTER}%"

if [ "$USAGE_AFTER" -gt 90 ]; then
    echo ""
    echo "⚠️ ATTENTION: L'espace disque est toujours critique (>90%)!"
    echo "Actions recommandées:"
    echo "  1. Supprimer d'anciens fichiers uploadés non utilisés"
    echo "  2. Exporter et archiver les vieilles soumissions"
    echo "  3. Augmenter la taille du disque dans Render (Settings > Disk)"
elif [ "$USAGE_AFTER" -gt 80 ]; then
    echo ""
    echo "⚠️ Attention: L'espace disque est élevé (>80%)"
    echo "Surveillez régulièrement l'utilisation"
else
    echo ""
    echo "✅ Espace disque OK (<80%)"
fi