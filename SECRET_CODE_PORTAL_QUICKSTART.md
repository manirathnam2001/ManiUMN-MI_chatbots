# Secret Code Portal - Quick Reference Card

## For Instructors

### Initial Setup (One-Time)

1. **Share Google Sheet with Service Account**
   - Sheet ID: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`
   - Share with: `mibots@umnsod-mibot.iam.gserviceaccount.com`
   - Permission: **Editor**

2. **Verify Headers**
   ```
   Table No | Name | Bot | Secret | Used | Role
   ```
   
   **Note**: The `Role` column is optional and supports three values:
   - `STUDENT` (default if empty)
   - `INSTRUCTOR` (single code unlocks all bots, never marked as used)
   - `DEVELOPER` (access to developer page and all apps)

### Adding a Student

1. Open the Google Sheet
2. Add new row:
   - **Table No**: Any identifier (1, 2, 3...)
   - **Name**: Student's full name
   - **Bot**: `OHI`, `HPV`, `TOBACCO`, or `PERIO`
   - **Secret**: Generate unique code (8-12 characters)
   - **Used**: `FALSE`
   - **Role**: Leave empty (defaults to STUDENT) or set to `STUDENT`, `INSTRUCTOR`, or `DEVELOPER`
3. Share the secret code with the student

### Adding an Instructor

1. Open the Google Sheet
2. Add new row:
   - **Table No**: Any identifier
   - **Name**: Instructor's full name
   - **Bot**: Can be any value (e.g., `ALL` or `OHI`) - instructors get access to all bots regardless of this value
   - **Secret**: Generate unique code (8-12 characters)
   - **Used**: Leave as `FALSE` (instructor codes are never marked as used during login)
   - **Role**: Set to `INSTRUCTOR`
3. Share the secret code with the instructor
4. **Note**: Instructor will see a bot selection screen to choose which bot to access

### Adding a Developer

1. Open the Google Sheet
2. Add new row:
   - **Table No**: Any identifier
   - **Name**: Developer's full name
   - **Bot**: Set to `DEVELOPER` (recommended for clarity, though value is ignored for developer role)
   - **Secret**: Generate unique code (8-12 characters)
   - **Used**: Leave as `FALSE` (developer codes are never marked as used during login)
   - **Role**: Set to `DEVELOPER`
3. Share the secret code with the developer
4. **Note**: Developer will have access to all apps and the developer page

### Generating Secret Codes

**Quick Methods:**
```bash
# Linux/Mac Terminal
openssl rand -base64 12

# Or use online tool:
# https://passwordsgenerator.net/
```

**Code Requirements:**
- Unique for each student
- 8-12 alphanumeric characters
- Mix of letters and numbers recommended

### Managing Students

**Reset a Code (Allow Re-Use)**
- Find student's row
- Change `Used` from `TRUE` to `FALSE`

**Check Who Used Their Code**
- Filter by `Used` column = `TRUE`

**Find Unused Codes**
- Filter by `Used` column = `FALSE`

**Disable a Code**
- Set `Used` to `TRUE`
- Or delete the row

### Portal URL

**Production**: [Your deployed portal URL]
**Local Test**: http://localhost:8501

### Student Instructions (Share This)

```
1. Go to the portal: [PORTAL_URL]
2. Enter your secret code
3. Click "Submit Code"
4. You'll be redirected to your assigned chatbot
```

### Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| Student says code doesn't work | Verify code exists, matches exactly (no spaces) |
| "Code already used" error | Check `Used` column, reset to FALSE if needed |
| Portal won't load data | Verify service account has access to sheet |
| Wrong bot assignment | Check `Bot` column value (OHI or HPV) |

### Support Contacts

**Technical Issues**: [Your IT contact]
**Portal Issues**: See SECRET_CODE_PORTAL_GUIDE.md for details

---

## For Students

### How to Access Your MI Practice Bot

1. **Get Your Code**
   - Your instructor will provide a secret code
   - This code is unique to you

2. **Go to Portal**
   - Visit: [PORTAL_URL]

3. **Enter Code**
   - Type or paste your secret code
   - Click "Submit Code"

4. **Access Chatbot**
   - You'll see a success message
   - Click the button to access your bot (OHI or HPV)

### Important Notes

- ⚠️ Codes can only be used **once**
- 🔒 Keep your code private (don't share)
- 📧 Contact your instructor if you have issues
- ♻️ If you need to access again, ask instructor to reset your code

### Common Issues

**"Invalid code"**
- Check for typos
- Make sure there are no spaces
- Verify with your instructor

**"Code already used"**
- You may have used it before
- Contact instructor for code reset or new code

**Button doesn't work?**
- Copy the URL shown
- Paste into your browser address bar
- Press Enter

---

## Quick Stats Template (for Reporting)

```
Semester: [Fall 2025]
Total Students: [  ]
Codes Generated: [  ]
Codes Used: [  ]
OHI Assignments: [  ]
HPV Assignments: [  ]
```

To get counts:
1. Open Google Sheet
2. Use `=COUNTIF(E:E,"TRUE")` for used codes
3. Use `=COUNTIF(C:C,"OHI")` for OHI assignments
4. Use `=COUNTIF(C:C,"HPV")` for HPV assignments
