#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID.}"

GCP_REGION="${GCP_REGION:-us-west1}"
GCP_ZONE="${GCP_ZONE:-us-west1-b}"
GCP_NETWORK="${GCP_NETWORK:-rovoca}"
GCP_SUBNET="${GCP_SUBNET:-rovoca-us-west1}"
GCP_DB_VM="${GCP_DB_VM:-rovoca-postgres}"
GCP_DB_NAME="${GCP_DB_NAME:-rovoca}"
GCP_DB_USER="${GCP_DB_USER:-rovoca}"
GCP_RUN_SERVICE_ACCOUNT="${GCP_RUN_SERVICE_ACCOUNT:-rovoca-run}"
GCP_ARTIFACT_REPOSITORY="${GCP_ARTIFACT_REPOSITORY:-rovoca}"
GCP_RUN_SERVICE="${GCP_RUN_SERVICE:-rovoca-api}"
GS_BUCKET_NAME="${GS_BUCKET_NAME:-${GCP_PROJECT_ID}-rovoca-media}"

RUN_SERVICE_ACCOUNT_EMAIL="${GCP_RUN_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/${GCP_ARTIFACT_REPOSITORY}/rovoca-api:$(date -u +%Y%m%d-%H%M%S)"
DB_INTERNAL_IP="$(gcloud compute instances describe "$GCP_DB_VM" \
  --project="$GCP_PROJECT_ID" \
  --zone="$GCP_ZONE" \
  --format='value(networkInterfaces[0].networkIP)')"

for secret_name in \
  rovoca-django-secret-key \
  rovoca-db-password \
  rovoca-jwt-private-key \
  rovoca-jwt-public-key \
  rovoca-kakao-aud \
  rovoca-google-aud; do
  gcloud secrets versions describe latest \
    --secret="$secret_name" \
    --project="$GCP_PROJECT_ID" >/dev/null
done

ENV_VARS="^|^DEBUG=False|DB_ENGINE=postgresql|DB_NAME=${GCP_DB_NAME}|DB_USER=${GCP_DB_USER}|DB_HOST=${DB_INTERNAL_IP}|DB_PORT=5432|DB_SSLMODE=require|DB_CONN_MAX_AGE=60|STORAGE_BACKEND=gcs|GS_PROJECT_ID=${GCP_PROJECT_ID}|GS_BUCKET_NAME=${GS_BUCKET_NAME}|GS_QUERYSTRING_AUTH=True|GS_IAM_SIGN_BLOB=True|GS_SA_EMAIL=${RUN_SERVICE_ACCOUNT_EMAIL}|ALLOWED_HOSTS=.run.app,api.rovoca.site|CSRF_TRUSTED_ORIGINS=https://*.run.app,https://api.rovoca.site"
SECRETS="SECRET_KEY=rovoca-django-secret-key:latest,DB_PASSWORD=rovoca-db-password:latest,JWT_PRIVATE_KEY=rovoca-jwt-private-key:latest,JWT_PUBLIC_KEY=rovoca-jwt-public-key:latest,KAKAO_AUD=rovoca-kakao-aud:latest,GOOGLE_AUD=rovoca-google-aud:latest"

gcloud builds submit . \
  --project="$GCP_PROJECT_ID" \
  --tag="$IMAGE"

gcloud run jobs deploy rovoca-migrate \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --image="$IMAGE" \
  --service-account="$RUN_SERVICE_ACCOUNT_EMAIL" \
  --command=python \
  --args=manage.py,migrate,--noinput \
  --set-env-vars="$ENV_VARS" \
  --set-secrets="$SECRETS" \
  --network="$GCP_NETWORK" \
  --subnet="$GCP_SUBNET" \
  --network-tags=rovoca-run \
  --vpc-egress=private-ranges-only \
  --tasks=1 \
  --max-retries=1 \
  --task-timeout=10m

gcloud run jobs execute rovoca-migrate \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --wait

gcloud run deploy "$GCP_RUN_SERVICE" \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --image="$IMAGE" \
  --service-account="$RUN_SERVICE_ACCOUNT_EMAIL" \
  --allow-unauthenticated \
  --set-env-vars="$ENV_VARS" \
  --set-secrets="$SECRETS" \
  --network="$GCP_NETWORK" \
  --subnet="$GCP_SUBNET" \
  --network-tags=rovoca-run \
  --vpc-egress=private-ranges-only \
  --cpu=1 \
  --memory=512Mi \
  --concurrency=20 \
  --min-instances=0 \
  --max-instances=2 \
  --timeout=60 \
  --cpu-throttling

SERVICE_URL="$(gcloud run services describe "$GCP_RUN_SERVICE" \
  --project="$GCP_PROJECT_ID" \
  --region="$GCP_REGION" \
  --format='value(status.url)')"

curl --fail --show-error --silent "${SERVICE_URL}/ready/"
echo
echo "Deployment ready: ${SERVICE_URL}"
