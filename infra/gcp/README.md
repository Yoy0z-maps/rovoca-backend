# GCP deployment

This deployment keeps PostgreSQL compatibility without using Cloud SQL:

```text
Internet -> Cloud Run (Django) -> Direct VPC egress -> private e2-micro (PostgreSQL)
                    |
                    +-> private Cloud Storage bucket (media and DB backups)
```

The defaults use `us-west1`, one `e2-micro`, one 30 GB `pd-standard` disk,
Cloud Run scale-to-zero, and a regional Cloud Storage bucket. The PostgreSQL VM
does not retain an external IPv4 address. During first provisioning only, it gets
a temporary address to install Debian packages; the script removes that address
on both success and failure.

## Prerequisites

- A GCP project with billing enabled
- Google Cloud CLI (`gcloud`) installed and authenticated
- A JWT key pair and Kakao audience value. For a fresh deployment, generate a
  new key pair instead of copying the AWS keys.
- Owner or equivalent permissions for Compute Engine, Cloud Run, IAM, Secret
  Manager, Cloud Build, Artifact Registry, and Cloud Storage

Do not generate a new JWT key pair during migration. Reusing the existing pair
keeps already-issued access and refresh tokens valid.

## 1. Authenticate

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## 2. Provision the free-tier-oriented foundation

```bash
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export GS_BUCKET_NAME=YOUR_GLOBALLY_UNIQUE_BUCKET_NAME
./infra/gcp/provision.sh
```

The script creates:

- A custom VPC and `us-west1` subnet
- Firewall access from the `rovoca-run` network tag to PostgreSQL only
- An IAP-only SSH rule
- A private `e2-micro` PostgreSQL VM and 30 GB standard persistent disk
- Cloud Run and database service accounts
- A private Cloud Storage bucket
- A Docker Artifact Registry repository
- An Artifact Registry cleanup policy that retains the latest two images
- Random database and Django secrets in Secret Manager
- A daily PostgreSQL backup timer with 14-day GCS retention

The generated database password is never printed. The database VM reads it from
Secret Manager using its attached service identity.

## 3. Upload application secrets

```bash
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export JWT_PRIVATE_KEY_FILE=/absolute/path/to/private.pem
export JWT_PUBLIC_KEY_FILE=/absolute/path/to/public.pem
export KAKAO_AUD_VALUE=YOUR_KAKAO_AUDIENCE
export GOOGLE_AUD_VALUE=YOUR_GOOGLE_WEB_CLIENT_ID
./infra/gcp/configure-secrets.sh
```

The script uploads new secret versions without printing their contents. Delete
temporary local copies of freshly generated keys after confirming the deployment.

## 4. Deploy and run migrations

```bash
export GCP_PROJECT_ID=YOUR_PROJECT_ID
export GS_BUCKET_NAME=YOUR_GLOBALLY_UNIQUE_BUCKET_NAME
./infra/gcp/deploy.sh
```

This builds one immutable image, runs Django migrations as a Cloud Run Job, then
deploys the API with 512 MiB memory, one CPU, zero minimum instances, and two
maximum instances. It finishes by requesting `/ready/`, which verifies the
private database connection.

## 5. Verify the fresh deployment

The deployment intentionally starts with an empty PostgreSQL database and an
empty private Cloud Storage bucket. Verify account creation, login, token refresh,
wordbook CRUD, image upload, and push-token registration before switching the
client or `api.rovoca.site`. AWS data and services are not accessed or modified.

## Operations

Check the API:

```bash
curl "$(gcloud run services describe rovoca-api --region=us-west1 --format='value(status.url)')/ready/"
```

Connect to PostgreSQL without a public IP:

```bash
gcloud compute ssh rovoca-postgres --zone=us-west1-b --tunnel-through-iap
```

Run and inspect a database backup:

```bash
gcloud compute ssh rovoca-postgres --zone=us-west1-b --tunnel-through-iap \
  --command='sudo systemctl start rovoca-postgres-backup.service'
gcloud storage ls "gs://${GS_BUCKET_NAME}/backups/postgres/"
```

GCP budget alerts do not stop spending, so keep Cloud Run's maximum instances and
service quotas restricted.
