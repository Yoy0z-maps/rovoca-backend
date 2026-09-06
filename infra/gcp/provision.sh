#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID to an existing project with billing enabled.}"

GCP_REGION="${GCP_REGION:-us-west1}"
GCP_ZONE="${GCP_ZONE:-us-west1-b}"
GCP_NETWORK="${GCP_NETWORK:-rovoca}"
GCP_SUBNET="${GCP_SUBNET:-rovoca-us-west1}"
GCP_SUBNET_CIDR="${GCP_SUBNET_CIDR:-10.10.0.0/24}"
GCP_DB_VM="${GCP_DB_VM:-rovoca-postgres}"
GCP_DB_NAME="${GCP_DB_NAME:-rovoca}"
GCP_DB_USER="${GCP_DB_USER:-rovoca}"
GCP_RUN_SERVICE_ACCOUNT="${GCP_RUN_SERVICE_ACCOUNT:-rovoca-run}"
GCP_DB_SERVICE_ACCOUNT="${GCP_DB_SERVICE_ACCOUNT:-rovoca-db}"
GCP_ARTIFACT_REPOSITORY="${GCP_ARTIFACT_REPOSITORY:-rovoca}"
GS_BUCKET_NAME="${GS_BUCKET_NAME:-${GCP_PROJECT_ID}-rovoca-media}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PASSWORD_SECRET="rovoca-db-password"
DJANGO_SECRET="rovoca-django-secret-key"
RUN_SERVICE_ACCOUNT_EMAIL="${GCP_RUN_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
DB_SERVICE_ACCOUNT_EMAIL="${GCP_DB_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

gcloud config set project "$GCP_PROJECT_ID"
gcloud services enable \
  artifactregistry.googleapis.com \
  billingbudgets.googleapis.com \
  cloudbuild.googleapis.com \
  compute.googleapis.com \
  iamcredentials.googleapis.com \
  iap.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com

ensure_service_account() {
  local name="$1"
  local display_name="$2"
  if ! gcloud iam service-accounts describe \
    "${name}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create "$name" --display-name="$display_name"
  fi
}

ensure_generated_secret() {
  local name="$1"
  if ! gcloud secrets describe "$name" >/dev/null 2>&1; then
    gcloud secrets create "$name" --replication-policy=automatic
    openssl rand -hex 32 | tr -d '\n' | \
      gcloud secrets versions add "$name" --data-file=-
  fi
}

ensure_service_account "$GCP_RUN_SERVICE_ACCOUNT" "Rovoca Cloud Run"
ensure_service_account "$GCP_DB_SERVICE_ACCOUNT" "Rovoca PostgreSQL VM"
ensure_generated_secret "$DB_PASSWORD_SECRET"
ensure_generated_secret "$DJANGO_SECRET"

gcloud secrets add-iam-policy-binding "$DB_PASSWORD_SECRET" \
  --member="serviceAccount:${DB_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" >/dev/null

for secret_name in "$DB_PASSWORD_SECRET" "$DJANGO_SECRET"; do
  gcloud secrets add-iam-policy-binding "$secret_name" \
    --member="serviceAccount:${RUN_SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null
done

if ! gcloud compute networks describe "$GCP_NETWORK" >/dev/null 2>&1; then
  gcloud compute networks create "$GCP_NETWORK" --subnet-mode=custom
fi

if ! gcloud compute networks subnets describe "$GCP_SUBNET" \
  --region="$GCP_REGION" >/dev/null 2>&1; then
  gcloud compute networks subnets create "$GCP_SUBNET" \
    --network="$GCP_NETWORK" \
    --region="$GCP_REGION" \
    --range="$GCP_SUBNET_CIDR" \
    --enable-private-ip-google-access
fi

if ! gcloud compute firewall-rules describe rovoca-cloud-run-to-postgres >/dev/null 2>&1; then
  gcloud compute firewall-rules create rovoca-cloud-run-to-postgres \
    --network="$GCP_NETWORK" \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:5432 \
    --source-tags=rovoca-run \
    --target-tags=rovoca-db
fi

if ! gcloud compute firewall-rules describe rovoca-iap-ssh >/dev/null 2>&1; then
  gcloud compute firewall-rules create rovoca-iap-ssh \
    --network="$GCP_NETWORK" \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=rovoca-db
fi

PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"
gcloud beta services identity create \
  --service=run.googleapis.com \
  --project="$GCP_PROJECT_ID" >/dev/null
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:service-${PROJECT_NUMBER}@serverless-robot-prod.iam.gserviceaccount.com" \
  --role="roles/compute.networkUser" >/dev/null

if ! gcloud storage buckets describe "gs://${GS_BUCKET_NAME}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${GS_BUCKET_NAME}" \
    --location="$GCP_REGION" \
    --uniform-bucket-level-access
fi

gcloud storage buckets update "gs://${GS_BUCKET_NAME}" \
  --public-access-prevention \
  --lifecycle-file="${SCRIPT_DIR}/storage-lifecycle.json" >/dev/null

gcloud storage buckets add-iam-policy-binding "gs://${GS_BUCKET_NAME}" \
  --member="serviceAccount:${RUN_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectUser" >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${GS_BUCKET_NAME}" \
  --member="serviceAccount:${DB_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/storage.objectCreator" >/dev/null

# Let the keyless Cloud Run identity create short-lived signed media URLs.
gcloud iam service-accounts add-iam-policy-binding "$RUN_SERVICE_ACCOUNT_EMAIL" \
  --member="serviceAccount:${RUN_SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/iam.serviceAccountTokenCreator" >/dev/null

if ! gcloud artifacts repositories describe "$GCP_ARTIFACT_REPOSITORY" \
  --location="$GCP_REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$GCP_ARTIFACT_REPOSITORY" \
    --repository-format=docker \
    --location="$GCP_REGION" \
    --description="Rovoca container images"
fi

gcloud artifacts repositories set-cleanup-policies "$GCP_ARTIFACT_REPOSITORY" \
  --project="$GCP_PROJECT_ID" \
  --location="$GCP_REGION" \
  --policy="${SCRIPT_DIR}/artifact-cleanup-policy.json" \
  --no-dry-run >/dev/null

detach_external_ip() {
  local access_config
  access_config="$(gcloud compute instances describe "$GCP_DB_VM" \
    --zone="$GCP_ZONE" \
    --format='value(networkInterfaces[0].accessConfigs[0].name)' 2>/dev/null || true)"
  if [[ -n "$access_config" ]]; then
    echo "Removing the temporary external IPv4 address from ${GCP_DB_VM}."
    gcloud compute instances delete-access-config "$GCP_DB_VM" \
      --zone="$GCP_ZONE" \
      --access-config-name="$access_config" \
      --quiet
  fi
}

if ! gcloud compute instances describe "$GCP_DB_VM" --zone="$GCP_ZONE" >/dev/null 2>&1; then
  trap detach_external_ip EXIT
  gcloud compute instances create "$GCP_DB_VM" \
    --zone="$GCP_ZONE" \
    --machine-type=e2-micro \
    --network-interface="network=${GCP_NETWORK},subnet=${GCP_SUBNET}" \
    --tags=rovoca-db \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-type=pd-standard \
    --boot-disk-size=30GB \
    --service-account="$DB_SERVICE_ACCOUNT_EMAIL" \
    --scopes=cloud-platform \
    --metadata="db-name=${GCP_DB_NAME},db-user=${GCP_DB_USER},db-password-secret=${DB_PASSWORD_SECRET},vpc-cidr=${GCP_SUBNET_CIDR},backup-bucket=${GS_BUCKET_NAME}" \
    --metadata-from-file="startup-script=${SCRIPT_DIR}/postgres-startup.sh,backup-script=${SCRIPT_DIR}/postgres-backup.sh"

  ready=false
  for _ in $(seq 1 60); do
    serial_output="$(gcloud compute instances get-serial-port-output "$GCP_DB_VM" \
      --zone="$GCP_ZONE" 2>/dev/null || true)"
    if grep -q "ROVOCA_POSTGRES_READY" <<<"$serial_output"; then
      ready=true
      break
    fi
    sleep 10
  done

  if [[ "$ready" != true ]]; then
    echo "PostgreSQL did not become ready within 10 minutes." >&2
    exit 1
  fi

  detach_external_ip
  trap - EXIT
else
  detach_external_ip
fi

DB_INTERNAL_IP="$(gcloud compute instances describe "$GCP_DB_VM" \
  --zone="$GCP_ZONE" \
  --format='value(networkInterfaces[0].networkIP)')"

echo
echo "GCP foundation is ready."
echo "Region: ${GCP_REGION}"
echo "Database internal IP: ${DB_INTERNAL_IP}"
echo "Media bucket: gs://${GS_BUCKET_NAME}"
echo "Next: upload the application secrets with configure-secrets.sh, then run deploy.sh."
