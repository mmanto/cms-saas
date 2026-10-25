#!/bin/sh
# Backup logico con retencion. Los dumps quedan en ./backups del host.
# Restore:  pg_restore --clean --if-exists -d "$DATABASE_URL" backups/<archivo>.dump
set -eu

: "${DATABASE_URL:?}"
: "${BACKUP_DIR:=/backups}"
: "${BACKUP_INTERVAL_SECONDS:=86400}"
: "${BACKUP_RETENTION_DAYS:=14}"

mkdir -p "$BACKUP_DIR"

while true; do
    stamp=$(date -u +%Y%m%dT%H%M%SZ)
    target="$BACKUP_DIR/${PGDATABASE:-cms_sas}_${stamp}.dump"

    if pg_dump --format=custom --no-owner --no-privileges --file="$target.partial" "$DATABASE_URL"; then
        mv "$target.partial" "$target"
        echo "[backup] ok $target"
    else
        echo "[backup] FALLO, descarto el archivo parcial" >&2
        rm -f "$target.partial"
    fi

    find "$BACKUP_DIR" -type f -name '*.dump' -mtime "+$BACKUP_RETENTION_DAYS" -delete
    find "$BACKUP_DIR" -type f -name '*.partial' -mtime +1 -delete

    sleep "$BACKUP_INTERVAL_SECONDS"
done
