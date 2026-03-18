#!/bin/bash
# Create Kubernetes secrets for the carduitive app
# Run this ONCE before deploying for the first time
#
# Usage: ./create-secrets.sh
#
# You must have kubectl configured and pointing at your GKE cluster.
# Required environment variables (or you will be prompted):
#   POSTGRES_USER, POSTGRES_PASSWORD
#   DATABASE_URL, SECRET_KEY
#   GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
#   FRONTEND_URL

set -euo pipefail

NAMESPACE="carduitive"

echo "=== Creating secrets for namespace: $NAMESPACE ==="

# Ensure namespace exists
kubectl get namespace "$NAMESPACE" >/dev/null 2>&1 || kubectl create namespace "$NAMESPACE"

# --- Postgres Secret ---
read -rp "Postgres username [postgres]: " PG_USER
PG_USER=${PG_USER:-postgres}

read -rsp "Postgres password: " PG_PASS
echo ""

if [ -z "$PG_PASS" ]; then
  echo "ERROR: Postgres password cannot be empty"
  exit 1
fi

kubectl create secret generic postgres-secret \
  --namespace="$NAMESPACE" \
  --from-literal=username="$PG_USER" \
  --from-literal=password="$PG_PASS" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✓ postgres-secret created"

# --- App Secrets ---
DB_URL="postgresql+asyncpg://${PG_USER}:${PG_PASS}@postgres:5432/carduitive"
echo "Database URL: $DB_URL"

read -rsp "Secret key (for JWT signing): " SECRET_KEY
echo ""
if [ -z "$SECRET_KEY" ]; then
  echo "ERROR: Secret key cannot be empty"
  exit 1
fi

read -rp "Google Client ID: " GOOGLE_CLIENT_ID
if [ -z "$GOOGLE_CLIENT_ID" ]; then
  echo "ERROR: Google Client ID cannot be empty"
  exit 1
fi

read -rsp "Google Client Secret: " GOOGLE_CLIENT_SECRET
echo ""
if [ -z "$GOOGLE_CLIENT_SECRET" ]; then
  echo "ERROR: Google Client Secret cannot be empty"
  exit 1
fi

read -rp "Frontend URL [https://carduitive.com]: " FRONTEND_URL
FRONTEND_URL=${FRONTEND_URL:-https://carduitive.com}

kubectl create secret generic app-secrets \
  --namespace="$NAMESPACE" \
  --from-literal=database-url="$DB_URL" \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=google-client-id="$GOOGLE_CLIENT_ID" \
  --from-literal=google-client-secret="$GOOGLE_CLIENT_SECRET" \
  --from-literal=frontend-url="$FRONTEND_URL" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✓ app-secrets created"

echo ""
echo "=== All secrets created successfully ==="
echo "You can now deploy with: kubectl apply -f k8s-ultra-cheap/"
