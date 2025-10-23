# GOOGLESA Credential Loading - Quick Reference

## Usage Examples

### Option 1: GOOGLESA_B64 (Recommended for Environment Variables)

**Why use this?** Avoids all shell escaping issues with newlines in the private_key field.

#### Creating the Base64 Value
```bash
# From a service account JSON file
cat your-service-account.json | base64 -w 0 > googlesa_b64.txt

# Set as environment variable
export GOOGLESA_B64=$(cat googlesa_b64.txt)
```

#### In Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: googlesa-secret
data:
  # Base64 encode the base64 string (double encoding is intentional for k8s)
  GOOGLESA_B64: <base64-of-base64-json>
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: GOOGLESA_B64
          valueFrom:
            secretKeyRef:
              name: googlesa-secret
              key: GOOGLESA_B64
```

#### In Docker
```bash
docker run -e GOOGLESA_B64="$(cat googlesa_b64.txt)" myapp
```

---

### Option 2: Streamlit Secrets (TOML Table)

**Why use this?** Best for Streamlit Cloud deployment, clean syntax.

#### In `.streamlit/secrets.toml`
```toml
[GOOGLESA]
type = "service_account"
project_id = "your-project"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYour\nMulti\nLine\nKey\n-----END PRIVATE KEY-----\n"
client_email = "your-sa@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

---

### Option 3: Streamlit Secrets (JSON String)

**Why use this?** Allows copying JSON directly from Google Cloud Console.

#### In `.streamlit/secrets.toml`
```toml
GOOGLESA = '{"type": "service_account", "project_id": "your-project", "private_key_id": "...", "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n", "client_email": "...", ...}'
```

---

### Option 4: GOOGLESA (Single-line JSON)

**Why use this?** Works for simple deployment scripts.

**Important:** Ensure `\n` escapes in private_key, not actual newlines!

```bash
export GOOGLESA='{"type": "service_account", "project_id": "your-project", "private_key": "-----BEGIN PRIVATE KEY-----\\nYour\\nKey\\n-----END PRIVATE KEY-----\\n", ...}'
```

---

### Option 5: Local File (Development)

**Why use this?** Easiest for local development.

Simply place `umnsod-mibot-ea3154b145f1.json` in the project root.

---

## Error Messages & Solutions

### Error: "Failed to parse GOOGLESA environment variable as JSON"

**Common Cause:** Unescaped newlines in the private_key field

**Solutions:**
1. Use `GOOGLESA_B64` instead (recommended)
2. Use Streamlit secrets
3. Ensure GOOGLESA uses `\n` escapes, not actual newlines

### Error: "Failed to decode GOOGLESA_B64 environment variable"

**Cause:** Invalid base64 encoding

**Solution:** Re-create the base64 string:
```bash
cat your-service-account.json | base64 -w 0
```

### Error: "No credentials found. Tried: ..."

**Cause:** No credential source is configured

**Solution:** Set up at least one of:
- Streamlit secrets
- GOOGLESA_B64 environment variable
- GOOGLESA environment variable
- Service account JSON file

---

## Debugging

To see which credential source is being used:

```python
if "googlesa_source" in st.session_state:
    st.info(f"Using credentials from: {st.session_state['googlesa_source']}")
```

Possible values:
- `"Streamlit secrets (TOML table)"`
- `"Streamlit secrets (JSON string)"`
- `"Environment variable (GOOGLESA_B64)"`
- `"Environment variable (GOOGLESA)"`
- `"Service account file (umnsod-mibot-ea3154b145f1.json)"`

---

## Priority Order

The system tries credential sources in this order:

1. **Streamlit secrets** (`st.secrets["GOOGLESA"]`)
2. **GOOGLESA_B64** environment variable
3. **GOOGLESA** environment variable
4. **Service account file**

The first successful source is used.

---

## Best Practices

### For Production (Kubernetes/Docker)
✅ Use **GOOGLESA_B64**
- No escaping issues
- Works reliably in all environments
- Easier to manage in secret stores

### For Streamlit Cloud
✅ Use **Streamlit secrets (TOML table)**
- Native format
- Easy to edit in UI
- Clear structure

### For Local Development
✅ Use **service account file**
- Simplest setup
- No configuration needed
- Keep file in `.gitignore`

### What NOT to do
❌ Don't use GOOGLESA with actual newlines in the value
❌ Don't commit service account files to git
❌ Don't hardcode credentials in source code
