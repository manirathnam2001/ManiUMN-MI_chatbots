# Secret Code Portal - Setup and Usage Guide

## Overview

The Secret Code Portal (`secret_code_portal.py`) provides a secure gateway for students to access the MI chatbots using instructor-provided codes.

## Google Sheet Structure

### Sheet Configuration
- **Sheet ID**: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`
- **Sheet Name**: `Sheet1`
- **Access**: Must share with `mibots@umnsod-mibot.iam.gserviceaccount.com` (Editor permissions)

### Required Columns

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| Table No | Text/Number | Student identifier | 1, 2, 3, Table-1, etc. |
| Name | Text | Student's full name | Alice Johnson, Bob Smith |
| Bot | Text | Bot assignment (case-insensitive) | OHI, HPV |
| Secret | Text | Unique access code | abc123, secret456 |
| Used | Boolean/Text | Whether code has been used | FALSE, TRUE |

### Example Sheet Data

```
Table No | Name           | Bot | Secret    | Used
---------|----------------|-----|-----------|------
1        | Alice Johnson  | OHI | abc123    | FALSE
2        | Bob Smith      | HPV | xyz789    | FALSE
3        | Charlie Brown  | OHI | test456   | TRUE
4        | Diana Prince   | HPV | super321  | FALSE
```

## Instructor Workflow

### Initial Setup

1. **Create/Access Google Sheet**
   - Use the existing sheet ID: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`
   - Or create a new sheet and update `SHEET_ID` in `secret_code_portal.py`

2. **Share with Service Account**
   - Click "Share" button in Google Sheets
   - Add: `mibots@umnsod-mibot.iam.gserviceaccount.com`
   - Grant **Editor** permissions
   - Uncheck "Notify people" if you don't want to send notification

3. **Set Up Headers**
   - First row must contain: `Table No`, `Name`, `Bot`, `Secret`, `Used`
   - Headers must match exactly (case-sensitive)

### Adding Students

1. **Generate Secret Codes**
   - Use a password generator for random codes
   - Recommended: 8-12 alphanumeric characters
   - Ensure codes are unique
   - Example tools:
     - `openssl rand -base64 12` (Linux/Mac)
     - Online: password-generator.org
     - Excel formula: `=CONCATENATE(CHAR(RANDBETWEEN(97,122)),CHAR(RANDBETWEEN(97,122)),...)`

2. **Add Student Row**
   ```
   Table No: [sequential number or identifier]
   Name: [Student's full name]
   Bot: [OHI or HPV]
   Secret: [generated unique code]
   Used: FALSE
   ```

3. **Distribute Codes**
   - Email codes to students individually
   - Include link to the portal
   - Remind students codes are single-use

### Managing Access

**Reset a Code (Allow Re-Use)**
- Find student's row
- Change "Used" column from TRUE to FALSE
- Student can now use the code again

**Disable a Code**
- Find student's row
- Change "Used" column to TRUE
- Or delete the entire row

**Check Usage**
- Review "Used" column
- TRUE = code has been used
- FALSE = code is still available

**Bulk Operations**
- Use Google Sheets' filter/sort features
- Example: Filter for Used=FALSE to see unused codes
- Example: Sort by Name to find specific students

## Student Workflow

1. **Receive Code**
   - Student receives secret code via email/learning platform

2. **Access Portal**
   - Navigate to portal URL
   - Portal loads with code entry form

3. **Enter Code**
   - Type secret code (hidden for privacy)
   - Click "Submit Code"

4. **Validation**
   - Portal checks code against Google Sheet
   - If valid and unused: success
   - If invalid: error message
   - If already used: error message

5. **Access Chatbot**
   - On success: code marked as used
   - Student redirected to assigned bot (OHI or HPV)
   - Can click button or copy URL

## Deployment Options

### Option 1: Local Development/Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the portal
streamlit run secret_code_portal.py

# Access at http://localhost:8501
```

### Option 2: Streamlit Cloud Deployment

1. **Push to GitHub**
   ```bash
   git add secret_code_portal.py
   git commit -m "Add secret code portal"
   git push
   ```

2. **Create Streamlit Cloud App**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select repository: `manirathnam2001/ManiUMN-MI_chatbots`
   - Set main file: `secret_code_portal.py`
   - Click "Deploy"

3. **Configure Secrets (Optional)**
   
   If you want to hide service account in secrets:
   
   - Go to app settings → Secrets
   - Add secret named `GOOGLE_SERVICE_ACCOUNT`
   - Paste entire JSON content of `umnsod-mibot-ea3154b145f1.json`
   - Update code to use secrets:
   
   ```python
   import json
   creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
   creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
   ```

4. **Update Bot URLs**
   - Edit `BOT_URLS` in `secret_code_portal.py`
   - Set to your deployed bot URLs
   - Redeploy if needed

### Option 3: Custom Domain/Server

For production deployment on custom infrastructure:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables (Optional)**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   export SHEET_ID=1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY
   ```

3. **Run with Custom Port**
   ```bash
   streamlit run secret_code_portal.py --server.port 8080
   ```

4. **Set Up Reverse Proxy (Optional)**
   - Use Nginx or Apache
   - Configure SSL/TLS certificates
   - Set up domain routing

## Security Best Practices

### Code Generation
- **Use Random Codes**: Don't use predictable patterns
- **Sufficient Length**: Minimum 8 characters
- **No Reuse**: Generate new codes each semester
- **Complexity**: Mix letters and numbers

### Access Control
- **Service Account**: Only share sheet with service account email
- **Limited Permissions**: Service account only needs Editor on specific sheet
- **Audit Access**: Regularly review who has access to Google Sheet
- **Rotate Credentials**: Consider rotating service account key periodically

### Monitoring
- **Check Usage**: Regularly review Used column
- **Detect Anomalies**: Look for unusual patterns
- **Student Feedback**: Listen to access issues reported by students
- **Logs**: Monitor application logs for errors

## Troubleshooting

### Common Issues

**1. "Failed to load code database"**
- **Cause**: Cannot connect to Google Sheets
- **Solution**: 
  - Verify sheet ID is correct
  - Check service account has access to sheet
  - Ensure internet connection is working
  - Verify credentials file exists

**2. "Invalid sheet format"**
- **Cause**: Column headers don't match expected format
- **Solution**: 
  - Check headers are exactly: `Table No`, `Name`, `Bot`, `Secret`, `Used`
  - Ensure no extra spaces or special characters
  - First row must be headers

**3. "Invalid code"**
- **Student Issue**: Code doesn't exist in sheet
- **Solution**:
  - Verify code was typed correctly
  - Check code exists in Google Sheet
  - Verify no leading/trailing spaces
  - Confirm code hasn't been deleted

**4. "Code already used"**
- **Student Issue**: Code has been used before
- **Solution**:
  - Check if student used it previously
  - Reset code if legitimate re-access needed
  - Generate new code if original was shared

**5. "Error marking code as used"**
- **Cause**: Permission issue with Google Sheets
- **Solution**:
  - Verify service account has Editor permissions
  - Check sheet isn't protected/locked
  - Verify API quotas haven't been exceeded

### Testing Access

**Test Service Account Access:**
```python
import gspread
from google.oauth2.service_account import Credentials

scope = ['https://spreadsheets.google.com/feeds', 
         'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(
    'umnsod-mibot-ea3154b145f1.json', scopes=scope)
client = gspread.authorize(creds)

# Try to access sheet
sheet = client.open_by_key('1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY')
print(f"Successfully connected to: {sheet.title}")
```

**Test Code Validation:**
- Add a test row with known code
- Use portal to validate
- Check if code is marked as used
- Reset for next test

## FAQ

**Q: Can students use the same code multiple times?**  
A: No, codes are single-use by default. Instructors can reset the "Used" flag to allow re-use.

**Q: Can I use different bot types besides OHI and HPV?**  
A: You would need to update the `BOT_URLS` dictionary and validation logic in the code.

**Q: How many students can I add?**  
A: Google Sheets supports up to 10 million cells, so thousands of students are supported.

**Q: Can I bulk import students?**  
A: Yes, use Google Sheets import features or copy-paste from Excel/CSV.

**Q: Is the service account file secure?**  
A: The file is included in the repository. For production, consider using Streamlit secrets or environment variables.

**Q: What if a student loses their code?**  
A: Look up their name in the sheet and provide the code again, or generate a new one.

**Q: Can I see when codes were used?**  
A: Currently no timestamp is recorded. You could add a "Used Date" column to track this.

**Q: Can codes expire?**  
A: Not automatically. You could add an "Expires" column and update validation logic.

## Support

For technical issues or questions:
- Check this documentation
- Review error messages carefully
- Test with a sample code first
- Contact repository maintainer if issues persist
