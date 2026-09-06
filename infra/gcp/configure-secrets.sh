#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID.}"
: "${JWT_PRIVATE_KEY_FILE:?Set JWT_PRIVATE_KEY_FILE to the existing private.pem path.}"
: "${JWT_PUBLIC_KEY_FILE:?Set JWT_PUBLIC_KEY_FILE to the existing public.pem path.}"
: "${KAKAO_AUD_VALUE:?Set KAKAO_AUD_VALUE to the existing Kakao audience value.}"
: "${GOOGLE_AUD_VALUE:?Set GOOGLE_AUD_VALUE to the Google web client ID.}"

GCP_RUN_SERVICE_ACCOUNT="${GCP_RUN_SERVICE_ACCOUNT:-rovoca-run}"
RUN_SERVICE_ACCOUNT_EMAIL="${GCP_RUN_SERVICE_ACCOUNT}@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

for key_file in "$JWT_PRIVATE_KEY_FILE" "$JWT_PUBLIC_KEY_FILE"; do
  if [[ ! -f "$key_file" ]]; then
    echo "Key file not found: ${key_file}" >&2
    exit 1
  fi
done

put_file_secret() {
  local name="$1"
  local source_file="$2"
  if ! gcloud secrets describe "$name" --project="$GCP_PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets create "$name" \
      --project="$GCP_PROJECT_ID" \
      --replication-policy=automatic
  fi
  gcloud secrets versions add "$name" \
    --project="$GCP_PROJECT_ID" \
    --data-file="$source_file"
}

put_value_secret() {
  local name="$1"
  local value="$2"
  if ! gcloud secrets describe "$name" --project="$GCP_PROJECT_ID" >/dev/null 2>&1; then
    gcloud secrets create "$name" \
      --project="$GCP_PROJECT_ID" \
      --replication-policy=automatic
  fi
  printf '%s' "$value" | gcloud secrets versions add "$name" \
    --project="$GCP_PROJECT_ID" \
    --data-file=-
}

put_file_secret rovoca-jwt-private-key "$JWT_PRIVATE_KEY_FILE"
put_file_secret rovoca-jwt-public-key "$JWT_PUBLIC_KEY_FILE"
put_value_secret rovoca-kakao-aud "$KAKAO_AUD_VALUE"
put_value_secret rovoca-google-aud "$GOOGLE_AUD_VALUE"

for secret_name in \
  rovoca-jwt-private-key \
  rovoca-jwt-public-key \
  rovoca-kakao-aud \
  rovoca-google-aud; do
  gcloud secrets add-iam-policy-binding "$secret_name" \
    --project="$GCP_PROJECT_ID" \
    --member="serviceAccount:${RUN_SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" >/dev/null
done

echo "Application secrets are ready. Secret values were not printed."
