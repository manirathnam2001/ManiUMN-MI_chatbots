# Secret Code Portal Implementation Summary

## Overview

Implemented a secure, single-use secret code portal system that allows instructors to control student access to MI chatbots (OHI and HPV) through Google Sheets-based code validation.

## Implementation Date

October 12, 2025

## Files Created

### 1. secret_code_portal.py (Main Application)
- **Lines**: 381
- **Purpose**: Streamlit web application for code validation and bot redirection
- **Key Features**:
  - Google Sheets integration using service account authentication
  - Single-use code validation with automatic marking
  - Dynamic routing to OHI or HPV bots
  - Real-time data refresh capability
  - Comprehensive error handling

### 2. SECRET_CODE_PORTAL_GUIDE.md (Comprehensive Documentation)
- **Lines**: 316
- **Purpose**: Complete setup, deployment, and troubleshooting guide
- **Sections**:
  - Google Sheet structure and setup
  - Instructor workflow
  - Student workflow
  - Deployment options (local, Streamlit Cloud, custom)
  - Security best practices
  - Troubleshooting guide
  - FAQ

### 3. SECRET_CODE_PORTAL_QUICKSTART.md (Quick Reference)
- **Lines**: 117
- **Purpose**: Quick reference card for instructors and students
- **Contents**:
  - One-time setup checklist
  - Adding students workflow
  - Code generation methods
  - Common troubleshooting
  - Student instructions template

## Files Modified

### 1. requirements.txt
**Added dependencies:**
```
# Google Sheets integration (for secret code portal)
gspread
google-auth
google-auth-oauthlib
```

### 2. README.md
**Added sections:**
- Updated main description to mention secret code portal
- Added secret_code_portal.py to project structure
- New section "🔐 Secret Code Portal" with:
  - Features overview
  - Google Sheet setup instructions
  - Service account configuration
  - Running and deployment instructions
  - Security best practices

## Technical Architecture

### Data Flow

```
Student enters code
    ↓
Streamlit UI validates input
    ↓
Google Sheets API query
    ↓
Validate code exists & unused
    ↓
Mark code as used (update sheet)
    ↓
Redirect to assigned bot
```

### Google Sheets Integration

**Authentication:**
- Method: Service account credentials
- File: `umnsod-mibot-ea3154b145f1.json`
- Service Account: `mibots@umnsod-mibot.iam.gserviceaccount.com`
- Required Scopes:
  - `https://spreadsheets.google.com/feeds`
  - `https://www.googleapis.com/auth/drive`

**Sheet Configuration:**
- Sheet ID: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`
- Sheet Name: `Sheet1`
- Required Permission: Editor (to mark codes as used)

**Data Structure:**
| Column | Purpose | Validation |
|--------|---------|------------|
| Table No | Student identifier | Any text/number |
| Name | Student full name | Text |
| Bot | Assignment (OHI/HPV) | Must be 'OHI' or 'HPV' (case-insensitive) |
| Secret | Unique access code | Any text (matched exactly) |
| Used | Usage status | FALSE/TRUE (or yes/no, 0/1) |

### Session State Management

**Variables:**
- `authenticated`: Boolean - whether user has valid code
- `redirect_info`: Dict - contains bot type and student name after validation
- `codes_data`: Dict - cached sheet data
  - `worksheet`: gspread Worksheet object
  - `headers`: List of column headers
  - `rows`: List of data rows
- `last_refresh`: Timestamp of last data reload

### Key Functions

**1. `get_google_sheets_client()`**
- Initializes and authenticates Google Sheets client
- Handles service account file validation
- Returns authorized gspread client

**2. `load_codes_from_sheet(force_refresh=False)`**
- Loads code data from Google Sheet
- Caches in session state for performance
- Validates sheet structure
- Returns success/failure boolean

**3. `validate_and_mark_code(secret_code)`**
- Searches for code in cached data
- Validates code is unused
- Validates bot type is valid (OHI or HPV)
- Marks code as used in Google Sheet
- Returns result dictionary with status and details

**4. `main()`**
- Streamlit UI layout and logic
- Form handling for code entry
- Success/error message display
- Redirect button generation

## Security Considerations

### Implemented Security Features

1. **Single-Use Codes**
   - Codes automatically marked as used after validation
   - Prevents code sharing among students

2. **Password Input Type**
   - Code entry field uses `type="password"`
   - Hides code from shoulder surfing

3. **Service Account Access**
   - Limited to specific sheet(s)
   - Editor permission only (not owner)
   - Can be revoked if compromised

4. **Input Validation**
   - Exact string matching (no fuzzy matching)
   - Bot type validation
   - Empty code rejection

5. **Error Messages**
   - Generic messages to prevent information leakage
   - No details about whether code exists or is just used

### Security Recommendations

1. **Code Generation**
   - Use cryptographically random codes
   - Minimum 8 characters
   - Mix of alphanumeric characters

2. **Distribution**
   - Send codes individually (not in groups)
   - Use secure channels (email, LMS)
   - Don't post codes publicly

3. **Monitoring**
   - Regular audit of "Used" column
   - Look for patterns of rapid sequential usage
   - Track any anomalies

4. **Credential Management**
   - Service account key is committed to repo
   - For production: use Streamlit secrets or env vars
   - Rotate credentials periodically

## Testing

### Unit Tests Created

**File**: `/tmp/test_secret_code_portal.py`

**Test Coverage**:
1. ✅ Bot URL configuration
2. ✅ Valid unused code (OHI)
3. ✅ Valid unused code (HPV)
4. ✅ Already used code rejection
5. ✅ Invalid code rejection
6. ✅ Cell update verification

**Test Results**: All tests passed

### Manual Testing Needed

Due to service account authentication issues in the test environment:
- [ ] Test with live Google Sheet access
- [ ] Verify code marking works in production
- [ ] Test redirect functionality
- [ ] Verify refresh button works
- [ ] Test error cases with real sheet

## Deployment Options

### Option 1: Streamlit Cloud (Recommended)
```bash
# Already pushed to GitHub
# Deploy via share.streamlit.io
# Set main file: secret_code_portal.py
```

### Option 2: Local Development
```bash
pip install -r requirements.txt
streamlit run secret_code_portal.py
```

### Option 3: Custom Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run with custom settings
streamlit run secret_code_portal.py \
  --server.port 8080 \
  --server.address 0.0.0.0
```

## Usage Workflow

### For Instructors

1. **Setup** (One-time)
   - Share sheet with service account
   - Verify headers match expected format

2. **Add Students**
   - Generate unique codes
   - Add rows to Google Sheet
   - Distribute codes to students

3. **Monitor**
   - Check "Used" column for utilization
   - Reset codes if needed
   - Generate reports

### For Students

1. Receive code from instructor
2. Navigate to portal URL
3. Enter code
4. Click submit
5. Redirected to assigned bot

## Performance Considerations

### Optimization

1. **Caching**
   - Sheet data cached in session state
   - Reduces API calls
   - Improves response time

2. **Refresh Strategy**
   - Manual refresh button
   - No auto-refresh to minimize API usage
   - Data loaded once per session by default

3. **API Rate Limits**
   - Google Sheets API: 100 requests per 100 seconds per user
   - Portal designed to minimize requests
   - Typically 2-3 requests per student (load + validate + update)

### Scalability

**Expected Load:**
- 50-200 students per semester
- 1-2 access periods per semester
- Low to moderate API usage

**Capacity:**
- Google Sheets: Up to 10 million cells
- Supports thousands of student records
- No server-side scaling needed (serverless via Streamlit Cloud)

## Maintenance

### Regular Tasks

**Weekly:**
- Check for student access issues
- Review error logs (if implemented)

**Per Semester:**
- Archive old codes
- Generate new codes for new students
- Update bot URLs if changed

**Annually:**
- Review and update documentation
- Consider credential rotation
- Update dependencies

### Monitoring Checklist

- [ ] Service account access still valid
- [ ] Sheet permissions correct
- [ ] Bot URLs still working
- [ ] No unusual access patterns
- [ ] Dependencies up to date

## Future Enhancements (Potential)

### Possible Additions

1. **Usage Timestamps**
   - Add "Used Date" column
   - Track when codes were used
   - Generate usage reports

2. **Code Expiration**
   - Add "Expires" column
   - Validate codes within date range
   - Auto-expire old codes

3. **Multiple Attempts Tracking**
   - Track failed attempts
   - Rate limiting per IP
   - Lockout after X failures

4. **Admin Dashboard**
   - Separate admin view
   - Real-time statistics
   - Bulk operations UI

5. **Email Notifications**
   - Send confirmation emails
   - Notify instructors of usage
   - Alert on suspicious activity

6. **Analytics**
   - Access patterns
   - Bot preference statistics
   - Completion rates

## Success Metrics

### Implementation Goals

- ✅ Secure single-use code system
- ✅ Google Sheets integration
- ✅ Automatic code marking
- ✅ Bot routing (OHI/HPV)
- ✅ Error handling
- ✅ Comprehensive documentation
- ✅ Quick reference guides
- ✅ Deployment instructions

### Acceptance Criteria Met

1. ✅ Code validation against Google Sheet
2. ✅ Single-use enforcement
3. ✅ Bot assignment routing
4. ✅ User-friendly error messages
5. ✅ Refresh data capability
6. ✅ Service account authentication
7. ✅ Complete documentation
8. ⚠️ Live testing (requires production credentials)

## Conclusion

The Secret Code Portal has been successfully implemented with comprehensive documentation, security considerations, and deployment options. The system is ready for deployment pending live testing with valid Google Sheets credentials.

All source code is clean, well-commented, and follows the existing project patterns. Documentation includes setup guides, troubleshooting, and quick reference materials for both instructors and students.

## Repository Changes Summary

**Files Added**: 3
- secret_code_portal.py
- SECRET_CODE_PORTAL_GUIDE.md
- SECRET_CODE_PORTAL_QUICKSTART.md

**Files Modified**: 2
- requirements.txt (added Google Sheets dependencies)
- README.md (added portal documentation)

**Total Lines Added**: ~1,100 lines of code and documentation

**Commits**: 2
1. "Add secret_code_portal.py with Google Sheets integration"
2. "Add comprehensive setup guide for secret code portal"
