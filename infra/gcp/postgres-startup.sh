#!/usr/bin/env bash
set -euo pipefail

metadata() {
  curl --fail --silent --show-error \
    --header "Metadata-Flavor: Google" \
    "http://metadata.google.internal/computeMetadata/v1/$1"
}

DB_NAME="$(metadata instance/attributes/db-name)"
DB_USER="$(metadata instance/attributes/db-user)"
DB_PASSWORD_SECRET="$(metadata instance/attributes/db-password-secret)"
VPC_CIDR="$(metadata instance/attributes/vpc-cidr)"
PROJECT_ID="$(metadata project/project-id)"

if [[ ! "$DB_NAME" =~ ^[a-z_][a-z0-9_]*$ ]]; then
  echo "Invalid database name" >&2
  exit 1
fi

if [[ ! "$DB_USER" =~ ^[a-z_][a-z0-9_]*$ ]]; then
  echo "Invalid database user" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install --yes --no-install-recommends ca-certificates curl postgresql python3

ACCESS_TOKEN="$({
  metadata instance/service-accounts/default/token
} | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"

SECRET_RESPONSE="$(curl --fail --silent --show-error \
  --header "Authorization: Bearer ${ACCESS_TOKEN}" \
  "https://secretmanager.googleapis.com/v1/projects/${PROJECT_ID}/secrets/${DB_PASSWORD_SECRET}/versions/latest:access")"

DB_PASSWORD="$(printf '%s' "$SECRET_RESPONSE" | python3 -c \
  'import base64,json,sys; print(base64.b64decode(json.load(sys.stdin)["payload"]["data"]).decode(), end="")')"

# The provisioning script generates a 64-character hexadecimal password. Keep
# this validation so secret contents can never be interpreted as SQL.
if [[ ! "$DB_PASSWORD" =~ ^[a-f0-9]{64}$ ]]; then
  echo "Database password secret has an unexpected format" >&2
  exit 1
fi

PG_CONFIG="$(sudo -u postgres psql -Atqc 'SHOW config_file')"
PG_HBA="$(sudo -u postgres psql -Atqc 'SHOW hba_file')"

if ! grep -q "BEGIN ROVOCA SETTINGS" "$PG_CONFIG"; then
  {
    echo
    echo "# BEGIN ROVOCA SETTINGS"
    echo "listen_addresses = '*'"
    echo "password_encryption = 'scram-sha-256'"
    echo "max_connections = 30"
    echo "shared_buffers = '128MB'"
    echo "effective_cache_size = '384MB'"
    echo "maintenance_work_mem = '32MB'"
    echo "work_mem = '4MB'"
    echo "# END ROVOCA SETTINGS"
  } >> "$PG_CONFIG"
fi

if ! grep -q "ROVOCA CLOUD RUN" "$PG_HBA"; then
  echo "hostssl ${DB_NAME} ${DB_USER} ${VPC_CIDR} scram-sha-256 # ROVOCA CLOUD RUN" >> "$PG_HBA"
fi

sudo -u postgres psql --set=ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE "${DB_USER}" LOGIN PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER ROLE "${DB_USER}" WITH LOGIN PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;
SQL

if ! sudo -u postgres psql -Atqc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
  sudo -u postgres createdb --owner="$DB_USER" "$DB_NAME"
fi

systemctl restart postgresql

metadata instance/attributes/backup-script > /usr/local/sbin/rovoca-postgres-backup
chmod 0750 /usr/local/sbin/rovoca-postgres-backup

cat > /etc/systemd/system/rovoca-postgres-backup.service <<'UNIT'
[Unit]
Description=Back up the Rovoca PostgreSQL database to Cloud Storage
After=postgresql.service network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/rovoca-postgres-backup
UNIT

cat > /etc/systemd/system/rovoca-postgres-backup.timer <<'UNIT'
[Unit]
Description=Run the Rovoca PostgreSQL backup every day

[Timer]
OnCalendar=*-*-* 18:00:00 UTC
Persistent=true
RandomizedDelaySec=10m

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now rovoca-postgres-backup.timer

unset ACCESS_TOKEN SECRET_RESPONSE DB_PASSWORD
echo "ROVOCA_POSTGRES_READY"
