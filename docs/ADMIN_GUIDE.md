# Admin Guide: Secret Code Portal Configuration

This guide explains how to configure the Secret Code Portal for production deployment.

## Overview

The Secret Code Portal requires access to a Google Sheets spreadsheet that stores access codes. This requires:

1. A Google Cloud service account with appropriate permissions
2. Configuration of credentials in your deployment environment
3. Sharing the spreadsheet with the service account

## Required Secrets

### Option 1: Streamlit Secrets (Recommended for Streamlit Cloud)

Add your service account credentials to Streamlit secrets. You can use either format:

#### TOML Table Format (Recommended)

In your Streamlit Cloud secrets or `.streamlit/secrets.toml`:

```toml
[GOOGLESA]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

#### Base64-Encoded JSON Format

If you prefer, you can base64-encode your entire service account JSON:

```bash
# Encode your service account JSON file
cat your-service-account.json | base64 -w 0
```

Then add to Streamlit secrets:

```toml
GOOGLESA_B64 = "eyJ0eXBlIjoic2VydmljZV9hY2NvdW50Ii..."
```

### Option 2: Environment Variables

For non-Streamlit deployments, use environment variables:

#### GOOGLESA_B64 (Recommended)

```bash
# Encode your service account JSON
export GOOGLESA_B64=$(cat your-service-account.json | base64 -w 0)
```

#### GOOGLESA (JSON String)

```bash
# Use single-line JSON with escaped newlines
export GOOGLESA='{"type":"service_account","private_key":"-----BEGIN...-----\\n",...}'
```

### Option 3: Service Account File (Local Development Only)

For local development, place the service account JSON file as:

```
umnsod-mibot-ea3154b145f1.json
```

in the application root directory.

## Google Sheet Configuration

### Required Sheet Structure

The portal expects a Google Sheet with the following structure:

| Table No | Name | Bot | Secret | Used |
|----------|------|-----|--------|------|
| 1 | John Doe | OHI | abc123 | FALSE |
| 2 | Jane Smith | HPV | xyz789 | TRUE |

**Columns:**
- **Table No**: Identifier for the row (any format)
- **Name**: Student's name
- **Bot**: Bot type - must be one of: `OHI`, `HPV`, `TOBACCO`, `PERIO`
- **Secret**: The access code (case-sensitive)
- **Used**: `TRUE` or `FALSE` (auto-updated when code is used)

### Sheet ID

The default sheet ID is configured in `secret_code_portal.py`:

```python
SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"
```

To use a different sheet, modify this value or set it via configuration.

### Sharing the Sheet

**Critical:** You must share the Google Sheet with your service account email:

1. Open the Google Sheet
2. Click "Share" in the top right
3. Enter your service account email (e.g., `your-account@your-project.iam.gserviceaccount.com`)
4. Grant **Editor** access (required for marking codes as used)
5. Click "Send" (uncheck "Notify people" if desired)

## Troubleshooting

### "Failed to load code database"

This error indicates the portal cannot connect to Google Sheets. Check:

1. **Missing Credentials**: Verify `GOOGLESA` or `GOOGLESA_B64` is set
2. **Invalid Credentials**: Ensure the JSON is valid and complete
3. **Sheet Not Shared**: Share the sheet with the service account email

### "Permission denied"

The service account doesn't have access to the sheet:

1. Verify the sheet is shared with the correct email
2. Ensure **Editor** access is granted (not just Viewer)
3. Check that the sheet ID is correct

### "Spreadsheet not found"

The sheet ID is incorrect or the sheet was deleted:

1. Verify the sheet exists
2. Check the sheet ID in the URL matches the configured ID
3. Ensure the sheet hasn't been moved to trash

### "Invalid sheet headers"

The sheet structure doesn't match expected format:

1. Verify the first row contains: `Table No`, `Name`, `Bot`, `Secret`, `Used`
2. Check for extra spaces or hidden characters
3. The headers are case-sensitive

### Network Errors

If you see network-related errors:

1. Verify internet connectivity
2. Check if Google APIs are accessible
3. Try the "Retry Loading" button
4. These errors often resolve on their own

## Creating a Service Account

If you need to create a new service account:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Go to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **Service Account**
5. Name your service account and click **Create**
6. Skip the optional steps and click **Done**
7. Click on the service account email
8. Go to **Keys** tab
9. Click **Add Key** > **Create new key**
10. Select **JSON** and click **Create**
11. Save the downloaded file securely

Then encode and configure as described above.

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** or Streamlit secrets for production
3. **Rotate keys periodically** and revoke old ones
4. **Limit service account permissions** to only what's needed
5. **Monitor access** via Google Cloud audit logs

## Support

If you continue to experience issues:

1. Check the application logs for detailed error messages
2. Verify all configuration steps above
3. Contact your system administrator
