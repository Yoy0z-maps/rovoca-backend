#!/usr/bin/env bash
set -euo pipefail

metadata() {
  curl --fail --silent --show-error \
    --header "Metadata-Flavor: Google" \
    "http://metadata.google.internal/computeMetadata/v1/$1"
}

DB_NAME="$(metadata instance/attributes/db-name)"
BACKUP_BUCKET="$(metadata instance/attributes/backup-bucket)"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OBJECT_NAME="backups/postgres/${DB_NAME}-${TIMESTAMP}.dump"
BACKUP_FILE="$(mktemp --suffix=.dump)"

cleanup() {
  rm -f "$BACKUP_FILE"
}
trap cleanup EXIT

runuser -u postgres -- pg_dump --format=custom "$DB_NAME" > "$BACKUP_FILE"

ACCESS_TOKEN="$({
  metadata instance/service-accounts/default/token
} | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"

ENCODED_BUCKET="$(python3 -c \
  'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' \
  "$BACKUP_BUCKET")"
ENCODED_OBJECT="$(python3 -c \
  'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' \
  "$OBJECT_NAME")"

curl --fail --silent --show-error \
  --request POST \
  --header "Authorization: Bearer ${ACCESS_TOKEN}" \
  --header "Content-Type: application/octet-stream" \
  --data-binary "@${BACKUP_FILE}" \
  "https://storage.googleapis.com/upload/storage/v1/b/${ENCODED_BUCKET}/o?uploadType=media&name=${ENCODED_OBJECT}" \
  >/dev/null

echo "Uploaded gs://${BACKUP_BUCKET}/${OBJECT_NAME}"
