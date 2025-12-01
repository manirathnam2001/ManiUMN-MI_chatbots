# MI Chatbot Portal - Administrator Guide

This guide provides deployment and configuration instructions for administrators of the MI Chatbot Portal.

## Table of Contents

1. [Google Sheets Setup](#google-sheets-setup)
2. [Service Account Configuration](#service-account-configuration)
3. [Deployment Secrets](#deployment-secrets)
4. [Sheet Column Layout](#sheet-column-layout)
5. [Troubleshooting](#troubleshooting)

---

## Google Sheets Setup

### Sheet Structure

The portal reads access codes from a Google Sheet with the following structure:

| Column | Name | Description | Required |
|--------|------|-------------|----------|
| A | Table No | Identifier for the table/group | Yes |
| B | Name | Student's full name | Yes |
| C | Bot | Bot type: OHI, HPV, TOBACCO, or PERIO | Yes |
| D | Secret | Unique secret code for access | Yes |
| E | Used | Whether the code has been used (TRUE/FALSE) | Yes |
| F | Role | User role: STUDENT, INSTRUCTOR, or DEVELOPER | No (defaults to STUDENT) |

### Example Sheet Layout

```
| Table No | Name            | Bot     | Secret   | Used  | Role       |
|----------|-----------------|---------|----------|-------|------------|
| 1        | Alice Johnson   | OHI     | ABC123   |       | STUDENT    |
| 2        | Bob Smith       | HPV     | DEF456   |       | STUDENT    |
| 3        | Dr. Carol White | OHI     | PROF001  |       | INSTRUCTOR |
| 4        | Dev Admin       | OHI     | DEV999   |       | DEVELOPER  |
```

### Sheet ID

The current sheet ID is: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`

---

## Service Account Configuration

### Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Navigate to **IAM & Admin** > **Service Accounts**
4. Click **Create Service Account**
5. Name it (e.g., `mi-chatbot-portal`)
6. Grant the role: **No role needed** (the service account only needs access to the specific sheet)
7. Click **Create Key** and select **JSON**
8. Download the JSON key file

### Step 2: Enable Google Sheets API

1. Go to **APIs & Services** > **Library**
2. Search for "Google Sheets API"
3. Click **Enable**

### Step 3: Share the Spreadsheet

1. Open your Google Sheet
2. Click **Share** in the top right
3. Paste the service account email (e.g., `mi-chatbot-portal@project-id.iam.gserviceaccount.com`)
4. Grant **Editor** access
5. Click **Share**

---

## Deployment Secrets

The portal supports multiple authentication methods (in priority order):

### Method 1: Streamlit Secrets (Recommended for Streamlit Cloud)

**TOML Table Format** (`~/.streamlit/secrets.toml` or Streamlit Cloud Secrets):

```toml
[GOOGLESA]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = """
-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
"""
client_email = "service-account@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

### Method 2: Base64-Encoded JSON (Recommended for Environment Variables)

**Creating the base64 string:**

```bash
# On Linux/Mac:
cat service-account.json | base64 -w 0

# On Windows (PowerShell):
[Convert]::ToBase64String([IO.File]::ReadAllBytes("service-account.json"))
```

**Setting in Streamlit Secrets:**

```toml
GOOGLESA_B64 = "eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6Li4ufQ=="
```

**Setting as Environment Variable:**

```bash
export GOOGLESA_B64="eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6Li4ufQ=="
```

### Method 3: JSON String Environment Variable

```bash
export GOOGLESA='{"type":"service_account","project_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",...}'
```

**Note:** Newlines in the private key must be escaped as `\n`.

### Method 4: Service Account File (Local Development)

Place the service account JSON file at:

```
umnsod-mibot-ea3154b145f1.json
```

---

## Sheet Column Layout

### Required Columns

| Column | Header Name | Description |
|--------|-------------|-------------|
| A | Table No | Group/table identifier |
| B | Name | Student's display name |
| C | Bot | One of: OHI, HPV, TOBACCO, PERIO |
| D | Secret | Unique access code |
| E | Used | TRUE, FALSE, YES, NO, 1, or empty |

### Optional Columns

| Column | Header Name | Description |
|--------|-------------|-------------|
| F | Role | STUDENT (default), INSTRUCTOR, or DEVELOPER |

### Role Descriptions

| Role | Description |
|------|-------------|
| **STUDENT** | Standard access. Code is marked as used after first login. |
| **INSTRUCTOR** | Infinite access. Code is never marked as used. Can access chatbots unlimited times. |
| **DEVELOPER** | Developer access. Redirects to Developer Tools page for testing. |

---

## Troubleshooting

### Error: "No Google Sheets credentials found"

**Cause:** The portal cannot find any valid credentials.

**Solution:**
1. Verify you've configured one of the authentication methods above
2. Check for typos in secret/environment variable names
3. For Streamlit Cloud: Verify secrets are properly configured in the app settings

### Error: "Malformed credentials"

**Cause:** The credentials are present but invalid or incorrectly formatted.

**Solution:**
1. For JSON strings: Ensure newlines in `private_key` are escaped as `\n`
2. For base64: Re-encode the file using `base64 -w 0`
3. For TOML: Use triple-quoted strings for the private key

### Error: "Permission denied when accessing spreadsheet"

**Cause:** The service account doesn't have access to the Google Sheet.

**Solution:**
1. The error message will display the service account email
2. Open the Google Sheet and share it with that email address
3. Grant **Editor** access (needed for marking codes as used)

### Error: "Missing required column: [column name]"

**Cause:** The sheet is missing a required column header.

**Solution:**
1. Verify the first row contains: Table No, Name, Bot, Secret, Used
2. Headers are case-sensitive and must match exactly
3. The Role column is optional

### Portal shows "Failed to load code database"

**Cause:** Could be multiple issues with sheet access.

**Solution:**
1. Click the "Retry" button to refresh
2. Check the browser console for error details
3. Verify the sheet ID matches the configured value
4. Ensure the sheet has at least 2 rows (header + 1 data row)

---

## Security Best Practices

1. **Never commit** service account JSON files to version control
2. Use **base64 encoding** for environment variables to avoid escaping issues
3. Rotate service account keys periodically
4. Grant **minimum necessary permissions** (Editor on specific sheet only)
5. Monitor access logs in Google Cloud Console

---

## Support

For additional support:
- Contact: UMN School of Dentistry IT
- Repository: Check the README.md and other documentation files

© 2025 UMN School of Dentistry - MI Practice Portal
