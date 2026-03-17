# Ultra-Cheap GCP Deployment Guide

## Cost: ~$20-25/month (vs $100+ for standard setup)

### Architecture
- 1x e2-micro node (us-east1) - $15/month
- In-cluster PostgreSQL with 5GB persistent disk
- NodePort services (no LoadBalancer fees)
- Cloudflare SSL (free)
- Google Artifact Registry (~$0.20/month)
- GCP Secret Manager for secrets (free tier: 10,000 access operations/month)

---

## Step 1: GCP Console Setup (Browser)

### 1.1 Create/Select Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project or select existing
3. Note the **Project ID** (you'll need this)

### 1.2 Enable Required APIs
Navigate to **APIs & Services > Library** and enable:
- [ ] Kubernetes Engine API
- [ ] Artifact Registry API
- [ ] Compute Engine API
- [ ] Secret Manager API

### 1.3 Create Artifact Registry Repository
1. Go to **Artifact Registry > Repositories**
2. Click **Create Repository**
3. Name: `carduitive3`
4. Format: Docker
5. Mode: Standard
6. Location: `us-east1`
7. Click **Create**

---

## Step 2: Create GKE Cluster (Browser)

1. Go to **Kubernetes Engine > Clusters**
2. Click **Create Cluster**
3. **Cluster basics:**
   - Name: `carduitive3-cluster`
   - Location type: Zonal
   - Zone: `us-east1-b`
4. **Node pools > default-pool:**
   - Number of nodes: **1**
   - Machine type: **e2-micro** (1 vCPU, 1GB memory)
   - Disk size: 20GB
5. **Networking:**
   - Enable HTTP load balancing: **OFF** (we're using NodePort)
6. Click **Create** (takes ~5 minutes)

---

## Step 3: Get Node External IP

After cluster is created:
1. Go to **Compute Engine > VM instances**
2. Find your node (name starts with `gke-carduitive3`)
3. Copy the **External IP** address

---

## Step 4: Cloudflare DNS Setup

### 4.1 Add Site to Cloudflare
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **Add Site**
3. Enter your domain
4. Select **Free** plan

### 4.2 DNS Records
Add an **A record**:
- Type: A
- Name: @ (or subdomain like `app`)
- IPv4 address: **Your GKE Node External IP**
- Proxy status: **Proxied** (orange cloud)
- TTL: Auto

### 4.3 SSL/TLS Settings
1. Go to **SSL/TLS**
2. Set **Encryption mode** to: **Full (strict)**

---

## Step 5: GitHub Secrets Setup

Go to your GitHub repo → **Settings > Secrets and variables > Actions**

Add these **Repository secrets**:

| Secret Name | Value |
|-------------|-------|
| `GCP_PROJECT_ID` | Your GCP Project ID |
| `GCP_SA_KEY` | Service Account JSON key (see below) |

### Create Service Account Key:
1. In GCP Console: **IAM & Admin > Service Accounts**
2. Click your compute service account (or create new)
3. **Keys > Add Key > Create new key**
4. Select **JSON**
5. Download and paste entire JSON into `GCP_SA_KEY` secret

---

## Step 6: Configure Secrets in GCP Secret Manager

### 6.1 Enable Secret Manager API
1. Go to **Secret Manager** in GCP Console
2. If not enabled, click **Enable API**

### 6.2 Create Database Password Secret
1. Click **Create Secret**
2. Name: `postgres-password`
3. Secret value: A strong password (e.g., generate with: `openssl rand -base64 32`)
4. Click **Create**

### 6.3 Create Application Secrets Secret
Create a secret named `app-secrets` with this JSON structure:

```json
{
  "database-url": "postgresql+asyncpg://postgres:YOUR_POSTGRES_PASSWORD@postgres:5432/carduitive3",
  "secret-key": "YOUR_64_CHAR_HEX_SECRET_KEY",
  "google-client-id": "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com",
  "google-client-secret": "YOUR_GOOGLE_CLIENT_SECRET",
  "frontend-url": "https://yourdomain.com"
}
```

**How to generate values:**
- `secret-key`: Run `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `google-client-id` & `google-client-secret`: From [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
- Replace `YOUR_POSTGRES_PASSWORD` with the same password from Step 6.2

---

## Step 7: Create Kubernetes Secrets from Secret Manager

After the cluster is running, you need to sync GCP Secret Manager secrets to Kubernetes.

### Option A: Using Cloud Shell (Recommended)

1. Open **Cloud Shell** in GCP Console (top right toolbar)
2. Connect to your cluster:
   ```bash
   gcloud container clusters get-credentials carduitive3-cluster --zone=us-east1-b
   ```

3. Create postgres-secret:
   ```bash
   # Get password from Secret Manager
   DB_PASSWORD=$(gcloud secrets versions access latest --secret=postgres-password)
   
   # Create Kubernetes secret
   kubectl create secret generic postgres-secret \
     --namespace=carduitive3 \
     --from-literal=username=postgres \
     --from-literal=password="$DB_PASSWORD"
   ```

4. Create app-secrets:
   ```bash
   # Get app secrets from Secret Manager
   APP_SECRETS=$(gcloud secrets versions access latest --secret=app-secrets)
   
   # Parse JSON and create Kubernetes secret
   echo "$APP_SECRETS" | jq -r 'to_entries | .[] | "\(.key)=\(.value)"' | \
   kubectl create secret generic app-secrets \
     --namespace=carduitive3 \
     --from-literal=database-url="$(echo "$APP_SECRETS" | jq -r '.database-url')" \
     --from-literal=secret-key="$(echo "$APP_SECRETS" | jq -r '.secret-key')" \
     --from-literal=google-client-id="$(echo "$APP_SECRETS" | jq -r '.google-client-id')" \
     --from-literal=google-client-secret="$(echo "$APP_SECRETS" | jq -r '.google-client-secret')" \
     --from-literal=frontend-url="$(echo "$APP_SECRETS" | jq -r '.frontend-url')"
   ```

5. Verify secrets created:
   ```bash
   kubectl get secrets -n carduitive3
   ```

### Option B: One-Step Script

Save this as `create-secrets.sh` and run in Cloud Shell:

```bash
#!/bin/bash
NAMESPACE=carduitive3

# Create namespace if doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Database secret
DB_PASSWORD=$(gcloud secrets versions access latest --secret=postgres-password)
kubectl create secret generic postgres-secret \
  --namespace=$NAMESPACE \
  --from-literal=username=postgres \
  --from-literal=password="$DB_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

# App secrets
APP_SECRETS=$(gcloud secrets versions access latest --secret=app-secrets)
kubectl create secret generic app-secrets \
  --namespace=$NAMESPACE \
  --from-literal=database-url="$(echo "$APP_SECRETS" | jq -r '.database-url')" \
  --from-literal=secret-key="$(echo "$APP_SECRETS" | jq -r '.secret-key')" \
  --from-literal=google-client-id="$(echo "$APP_SECRETS" | jq -r '.google-client-id')" \
  --from-literal=google-client-secret="$(echo "$APP_SECRETS" | jq -r '.google-client-secret')" \
  --from-literal=frontend-url="$(echo "$APP_SECRETS" | jq -r '.frontend-url')" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets created successfully!"
kubectl get secrets -n $NAMESPACE
```

---

## Step 8: Update Google OAuth Redirect URIs

1. Go to [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your OAuth 2.0 Client ID
3. Add to **Authorized redirect URIs**:
   ```
   https://yourdomain.com/api/auth/google/callback
   ```
4. Add to **Authorized JavaScript origins**:
   ```
   https://yourdomain.com
   ```

---

## Step 9: Deploy!

### Option A: Automatic (GitHub Actions)
1. Commit and push changes
2. Go to **Actions** tab in GitHub
3. Run workflow: **Deploy to GKE (Ultra-Cheap)**

### Option B: Manual Deployment
If you prefer manual control, you can deploy from Cloud Shell:

```bash
# Connect to cluster
gcloud container clusters get-credentials carduitive3-cluster --zone=us-east1-b

# Apply manifests (apply secrets first!)
kubectl apply -f k8s-ultra-cheap/00-namespace.yaml
kubectl apply -f k8s-ultra-cheap/01-postgres-pvc.yaml
kubectl apply -f k8s-ultra-cheap/02-postgres-deployment.yaml
kubectl apply -f k8s-ultra-cheap/03-postgres-service.yaml
kubectl apply -f k8s-ultra-cheap/04-backend-deployment.yaml
kubectl apply -f k8s-ultra-cheap/05-backend-service.yaml
kubectl apply -f k8s-ultra-cheap/06-frontend-deployment.yaml
kubectl apply -f k8s-ultra-cheap/07-frontend-service.yaml

# Check status
kubectl get pods -n carduitive3
kubectl get services -n carduitive3
```

---

## Step 10: Verify Deployment

1. Check pods are running:
   ```
   kubectl get pods -n carduitive3
   ```

2. Get NodePort URLs:
   ```
   kubectl get svc -n carduitive3
   ```
   
   You should see:
   - frontend: `30081/TCP`
   - backend: `30080/TCP`

3. Test your domain:
   ```
   https://yourdomain.com
   ```

---

## Troubleshooting

### Pods stuck in Pending
- Check: `kubectl describe pod <pod-name> -n carduitive3`
- Likely cause: Insufficient resources on e2-micro
- Solution: Reduce resource requests in deployment files

### Cannot access site
- Verify Cloudflare A record points to correct Node IP
- Check: `kubectl get nodes -o wide` (should show EXTERNAL-IP)
- Ensure Cloudflare proxy is enabled (orange cloud)

### Database connection errors
- Check secrets exist: `kubectl get secrets -n carduitive3`
- Verify secret values: `kubectl get secret app-secrets -n carduitive3 -o jsonpath='{.data}' | base64 -d`
- Check initContainer waited for postgres: `kubectl logs deployment/backend -n carduitive3`

### OAuth not working
- Verify redirect URI in Google Console matches exactly (including https://)
- Check `frontend-url` secret value includes `https://`
- Ensure OAuth credentials are from the same GCP project

---

## Maintenance

### Update deployment:
Just push to `main` branch - GitHub Actions will rebuild and deploy automatically.

### Update secrets:
1. Update value in GCP Secret Manager
2. Re-run the secret creation command in Cloud Shell to sync to Kubernetes

### View logs:
```bash
kubectl logs deployment/backend -n carduitive3 -f
kubectl logs deployment/frontend -n carduitive3 -f
kubectl logs deployment/postgres -n carduitive3 -f
```

### Restart a pod:
```bash
kubectl rollout restart deployment/backend -n carduitive3
```

### Database backup (manual):
```bash
kubectl exec -it deployment/postgres -n carduitive3 -- pg_dump -U postgres carduitive3 > backup.sql
```

---

## Costs Summary

| Component | Monthly Cost |
|-----------|-------------|
| 1x e2-micro node | ~$15 |
| 5GB persistent disk | ~$0.20 |
| Artifact Registry | ~$0.10 |
| Secret Manager (10K ops) | Free |
| Egress (minimal) | ~$1-5 |
| **Total** | **~$17-21** |

---

## Important Notes

⚠️ **Single node**: If the node restarts (monthly maintenance), expect ~2-3 minutes downtime

⚠️ **No auto-backups**: Database runs in-cluster. Back up manually or risk data loss

⚠️ **Resource limits**: e2-micro has 1GB RAM. If you add more features, you may need to upgrade to e2-small (~$25/month)

✅ **SSL included**: Free via Cloudflare

✅ **Custom domain**: Works with your own domain

✅ **Secrets security**: All sensitive data stored in GCP Secret Manager, never in git

---

You're all set! 🚀
