# MI Chatbot Portal - Administrator Guide

This guide explains how to manage access codes, roles, and the Google Sheet structure for the MI Chatbot Portal.

## Table of Contents

1. [Google Sheet Structure](#google-sheet-structure)
2. [Access Code Roles](#access-code-roles)
3. [Creating Access Codes](#creating-access-codes)
4. [Role-Specific Behavior](#role-specific-behavior)
5. [Developer Tools](#developer-tools)
6. [Troubleshooting](#troubleshooting)

---

## Google Sheet Structure

The portal reads access codes from a Google Sheet with the following structure:

| Column | Name | Description | Example |
|--------|------|-------------|---------|
| A | Table No | Unique identifier for the code | 1, 2, 3... |
| B | Name | User's display name | John Doe |
| C | Bot | Assigned chatbot type | OHI, HPV, TOBACCO, PERIO |
| D | Secret | The secret access code | ABC123XYZ |
| E | Used | Whether code has been used | TRUE/FALSE |
| F | Role | User role (optional) | Student, Instructor, Developer |

### Column Details

- **Table No**: Any unique identifier. Used for reference only.
- **Name**: The user's name. Displayed in welcome messages and PDF reports.
- **Bot**: The chatbot the user is assigned to. Must be one of:
  - `OHI` - Oral Hygiene Instruction
  - `HPV` - HPV Vaccine Counseling
  - `TOBACCO` - Tobacco Cessation
  - `PERIO` - Periodontitis Counseling
- **Secret**: A unique code that users enter to gain access. Should be hard to guess.
- **Used**: Set to `FALSE` initially. Changed to `TRUE` when a student uses the code.
- **Role**: (Optional) User role. If empty or not present, defaults to `Student`.

---

## Access Code Roles

The portal supports three user roles:

### 1. Student (Default)

- **Single use**: Code is marked as used after first login
- **Bot restriction**: Can only access their assigned bot
- **Typical users**: Students practicing MI skills

**Example row:**
```
| 1 | Jane Smith | OHI | STUDENT001 | FALSE | Student |
```

### 2. Instructor

- **Infinite use**: Code is never marked as used
- **All bots**: Can access all chatbots (OHI, HPV, TOBACCO, PERIO)
- **Typical users**: Faculty, teaching assistants, course administrators

**Example row:**
```
| 100 | Dr. Johnson | OHI | INSTRUCTOR2024 | FALSE | Instructor |
```

Note: The Bot column value doesn't matter for instructors since they have access to all bots.

### 3. Developer

- **Reusable**: Code is never marked as used
- **Developer page**: Access to the Developer Tools page
- **Typical users**: Technical staff, system administrators

**Example row:**
```
| 999 | Admin Dev | DEVELOPER | DEVACCESS2024 | FALSE | Developer |
```

---

## Creating Access Codes

### For Students

1. Open the Google Sheet
2. Add a new row with:
   - Unique Table No
   - Student's name
   - Assigned bot (OHI, HPV, TOBACCO, or PERIO)
   - Unique secret code
   - `FALSE` in the Used column
   - `Student` in the Role column (or leave blank)

### For Instructors

1. Add a row with:
   - Any bot type (will have access to all)
   - Unique secret code
   - `FALSE` in Used column
   - `Instructor` in the Role column

### For Developers

1. Add a row with:
   - `DEVELOPER` as the bot type
   - Unique secret code
   - `FALSE` in Used column
   - `Developer` in the Role column

### Best Practices for Secret Codes

- Use random strings (8-12 characters)
- Mix letters and numbers
- Avoid common words or patterns
- Consider using a password generator
- Example formats: `X7mK9pQ2`, `STU-2024-ABC`, `OHI-Smith-7842`

---

## Role-Specific Behavior

### Student Access Flow

1. Student enters their name, Groq API key, and secret code
2. Portal validates the code:
   - Checks if code exists in sheet
   - Checks if code is not already used
   - Validates bot assignment matches
3. Session state is set (authenticated, assigned bot)
4. Code is marked as `TRUE` in the Used column
5. Student is redirected to their assigned bot page

### Instructor Access Flow

1. Instructor enters credentials and secret code
2. Portal validates the code:
   - Checks if code exists in sheet
   - Identifies role as Instructor
3. Session state is set with INSTRUCTOR role
4. Code is **NOT** marked as used
5. Instructor is redirected to any bot (default: OHI)
6. Instructor can navigate to any other bot freely

### Developer Access Flow

1. Developer enters credentials and secret code
2. Portal validates the code:
   - Checks if code exists in sheet
   - Identifies role as Developer
3. Session state is set with DEVELOPER role
4. Code is **NOT** marked as used
5. Developer is redirected to the Developer Tools page

---

## Developer Tools

The Developer page (`pages/developer_page.py`) provides testing utilities:

### 1. Send Test Email

Tests the email sending functionality:
- Verifies SMTP configuration
- Tests connection to email server
- Useful for diagnosing email backup issues

### 2. Generate Test PDF

Tests PDF generation:
- Creates a sample MI feedback PDF
- Verifies the PDF generation pipeline
- Provides a downloadable test PDF

### 3. Mark Code Used in Sheet

Tests Google Sheets integration:
- Finds a code in the sheet
- Marks it as used
- Useful for testing sheet write permissions

**⚠️ Warning**: This action actually modifies the Google Sheet!

---

## Troubleshooting

### Common Issues

#### "Code has already been used"
- **Cause**: A student code was already used
- **Solution**: 
  - Change the Used column back to `FALSE`, OR
  - Create a new code for the user

#### "Access Denied: You are not authorized for this chatbot"
- **Cause**: Student is trying to access a different bot than assigned
- **Solution**: 
  - Direct user to correct bot, OR
  - Update their Bot assignment in the sheet

#### "Invalid bot type in the sheet"
- **Cause**: Bot column contains an unrecognized value
- **Solution**: Ensure Bot column contains exactly one of: OHI, HPV, TOBACCO, PERIO

#### Developer page shows "Access Denied"
- **Cause**: User role is not set to Developer
- **Solution**: 
  - Check that the Role column contains `Developer` (case-insensitive)
  - Verify the user is using the correct code

### Checking Authentication Status

The Developer page shows session information:
- `authenticated`: Whether user is logged in
- `user_role`: Current role (STUDENT, INSTRUCTOR, DEVELOPER)
- `student_name`: User's display name
- `redirect_info`: Bot assignment information

---

## Security Notes

1. **Secret codes** should be distributed securely (not posted publicly)
2. **Instructor codes** provide access to all bots - distribute carefully
3. **Developer codes** provide system access - limit to technical staff
4. The Google Sheet should have restricted sharing permissions
5. Service account credentials should be kept secure

---

## Support

For technical issues with the portal:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review application logs for error messages
3. Contact the system administrator

For user access issues:
1. Verify the user's code in the Google Sheet
2. Check the Used and Role columns
3. Issue a new code if necessary
