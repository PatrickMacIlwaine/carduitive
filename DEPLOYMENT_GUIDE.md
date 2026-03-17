# Ultra-Cheap GCP Deployment Guide

## Cost: ~$20-25/month (vs $100+ for standard setup)

### Architecture
- 1x e2-micro node (us-east1) - $15/month
- In-cluster PostgreSQL with 5GB persistent disk
- NodePort services (no LoadBalancer fees)
- Cloudflare SSL (free)
- Google Artifact Registry (~$0.20/month)

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

## Step 6: Configure Secrets File

Edit `k8s-ultra-cheap/08-secrets.yaml`:

```bash
# Replace these values:
# 1. Strong password for PostgreSQL
# 2. Generate SECRET_KEY: python3 -c "import secrets; print(secrets.token_hex(32))"
# 3. Your Google OAuth credentials from console.cloud.google.com/apis/credentials
# 4. Your domain (e.g., https://yourdomain.com)
```

---

## Step 7: Update Google OAuth Redirect URIs

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

## Step 8: Deploy!

### Option A: Automatic (GitHub Actions)
1. Commit and push changes
2. Go to **Actions** tab in GitHub
3. Run workflow: **Deploy to GKE (Ultra-Cheap)**

### Option B: Manual Deployment
If you prefer manual control, you can deploy from Cloud Shell:

```bash
# Connect to cluster
gcloud container clusters get-credentials carduitive3-cluster --zone=us-east1-b

# Apply manifests
kubectl apply -f k8s-ultra-cheap/

# Check status
kubectl get pods -n carduitive3
kubectl get services -n carduitive3
```

---

## Step 9: Verify Deployment

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
- Check secrets are applied: `kubectl get secrets -n carduitive3`
- Verify initContainer waited for postgres: `kubectl logs deployment/backend -n carduitive3`

### OAuth not working
- Verify redirect URI in Google Console matches exactly
- Check `FRONTEND_URL` secret matches your domain with `https://`

---

## Maintenance

### Update deployment:
Just push to `main` branch - GitHub Actions will rebuild and deploy automatically.

### View logs:
```bash
kubectl logs deployment/backend -n carduitive3 -f
kubectl logs deployment/frontend -n carduitive3 -f
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
| Egress (minimal) | ~$1-5 |
| **Total** | **~$17-21** |

---

## Important Notes

⚠️ **Single node**: If the node restarts (monthly maintenance), expect ~2-3 minutes downtime

⚠️ **No auto-backups**: Database runs in-cluster. Back up manually or risk data loss

⚠️ **Resource limits**: e2-micro has 1GB RAM. If you add more features, you may need to upgrade to e2-small (~$25/month)

✅ **SSL included**: Free via Cloudflare

✅ **Custom domain**: Works with your own domain

---

You're all set! 🚀
