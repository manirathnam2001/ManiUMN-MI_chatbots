# MI Chatbots

This repository contains a **production-ready multipage Streamlit application** for Motivational Interviewing (MI) practice with secure student access:

- `secret_code_portal.py`: **Main entry point** - Secure access portal for student authentication
- `pages/OHI.py`: Practice MI skills for **Oral Hygiene** (internal page)
- `pages/HPV.py`: Practice MI skills related to **HPV vaccine** (internal page)

**Architecture**: The app uses Streamlit's multipage structure with internal navigation (`st.switch_page`) to eliminate redirect loops and improve security. Students enter their credentials once at the portal and are seamlessly navigated to their assigned chatbot.

These chatbots simulate realistic patient interactions and provide **automated MI feedback** based on a **40-point binary rubric system**.
We use **Groq LLMs** for real-time dialogue and **retrieval-augmented generation (RAG)** to incorporate structured feedback from rubric documents.

## 🎯 New MI Rubric (40 Points)

The chatbots now use a comprehensive **40-point binary assessment rubric** with 6 categories:

| Category | Points | Description |
|----------|--------|-------------|
| **Collaboration** | 9 | Partnership building and rapport |
| **Acceptance** | 6 | Respect, autonomy, reflective listening |
| **Compassion** | 6 | Non-judgmental, empathetic approach |
| **Evocation** | 6 | Elicit self-efficacy and intrinsic motivation |
| **Summary** | 3 | Reflective summarization |
| **Response Factor** | 10 | Timeliness and intuitiveness |

**Binary Scoring**: Each category is assessed as either "Meets Criteria" (full points) or "Needs Improvement" (0 points).

📖 **See [docs/MI_Rubric.md](docs/MI_Rubric.md) for complete rubric documentation, criteria details, API usage, and example payloads.**

---
## 📁 Project Structure

    ManiUMN-MI_chatbots/
    ├── .devcontainer/         # Dev Container setup (for VS Code Remote/Containers)
    ├── hpv_rubrics/           # HPV MI example transcripts + rubric feedback (.txt format)
    ├── ohi_rubrics/           # Oral Hygiene MI transcripts + rubric feedback (.txt format)
    ├── pages/                 # Streamlit multipage app pages (internal navigation)
    │   ├── OHI.py             # Oral Health MI chatbot (access via portal)
    │   └── HPV.py             # HPV vaccine MI chatbot (access via portal)
    ├── secret_code_portal.py  # Main entry point - Secret code access portal
    ├── HPV.py                 # Legacy standalone HPV app (deprecated)
    ├── OHI.py                 # Legacy standalone OHI app (deprecated)
    ├── chat_utils.py          # Shared chat handling utilities
    ├── pdf_utils.py           # PDF report generation utilities
    ├── feedback_template.py   # Standardized feedback formatting
    ├── scoring_utils.py       # MI component scoring and validation
    ├── time_utils.py          # Timezone handling utilities
    ├── config_loader.py       # Configuration and environment variable management
    ├── email_utils.py         # Email sending utilities (optional Box integration)
    ├── umnsod-mibot-ea3154b145f1.json  # Service account credentials for Google Sheets
    ├── README.md              # This file - setup and usage instructions
    ├── requirements.txt       # Python dependencies (optimized)
    ├── runtime.txt            # Python version for deployment environments
    └── .env.example           # Example environment variables file

> You can add more `.txt` transcripts with MI feedback in the `hpv_rubrics/` or `ohi_rubrics/` folders to improve the RAG-based evaluation.

---

## 📧 Box Email Backup Feature

**NEW**: Automatic PDF backup to Box via email!

Both OHI and HPV applications now automatically back up generated PDF feedback reports to Box email addresses. This feature provides:

- **Automatic Backup**: PDFs are emailed to Box after generation
- **Fail-Safe Design**: PDF download always works, even if email fails
- **Retry Mechanism**: 3 automatic retry attempts with 5-second delays
- **Comprehensive Logging**: Daily rotating logs in "SMTP logs" directory
- **User Notifications**: Clear success/failure messages in the UI

### Configuration

The feature is configured in `config.json`:
- **OHI Box Email**: OHI_dir.zcdwwmukjr9ab546@u.box.com
- **HPV Box Email**: HPV_Dir.yqz3brxlhcurhp2l@u.box.com
- **SMTP Server**: smtp.gmail.com:587 with SSL/TLS

### Documentation

See [BOX_EMAIL_BACKUP.md](BOX_EMAIL_BACKUP.md) for detailed documentation including:
- Configuration options
- Log format and examples
- Error handling
- Troubleshooting guide
- Security considerations

### Testing

Run the test suite to verify the email backup system:
```bash
python3 test_box_email_backup.py
```

---

## 🧬 HPV MI Practice App

This app simulates a realistic patient interaction to practice Motivational Interviewing (MI) skills for HPV vaccination discussions. Users can play the role of a patient or provider to engage in a conversation that focuses on exploring thoughts and feelings about the HPV vaccine.


Checkout the app here : [![Open HPV MI chatbot in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hpvmiapp.streamlit.app/)


## 🦷 OHI MI Practice App
This app simulates a realistic dental hygiene patient interaction to help users—particularly dental students—practice **Motivational Interviewing (MI)** skills related to **oral hygiene and behavior change**.

The patient (played by AI) begins with scenarios (e.g., "I’ve noticed these yellow spots...") and reacts naturally to the student’s MI techniques. At the end of the session, the system evaluates the student's performance using an MI rubric and provides detailed, constructive feedback.

Checkout the app here : [![Open OHI MI Chatbot in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ohimiapp.streamlit.app/)


## 🔐 Secret Code Portal (Multipage App Entry)

The **Secret Code Portal** (`secret_code_portal.py`) is the **main entry point** for the production-ready multipage Streamlit application. It provides a secure access gateway where students authenticate once and are seamlessly navigated to their assigned chatbot.

### Key Features
- **Centralized Authentication**: Students enter credentials (name, API key, secret code) once at the portal
- **Code Validation**: Validates secret codes against a Google Sheet database
- **Single-Use Codes**: Automatically marks codes as used to prevent sharing
- **Smart Internal Routing**: Uses `st.switch_page()` to navigate to OHI or HPV pages without external URLs
- **Session-Based Security**: Maintains authentication state across pages
- **Real-Time Updates**: Refresh button to reload the latest data from Google Sheets
- **Cached Access**: Google Sheets client and data are cached to reduce API calls
- **Clear Feedback**: User-friendly error messages for invalid or already-used codes

### Architecture & Navigation
- **Portal Flow**: Student enters all credentials at `secret_code_portal.py`
- **Internal Navigation**: Uses Streamlit's `st.switch_page("pages/OHI.py")` for seamless transitions
- **No External URLs**: Bot URLs are never exposed to students
- **Session State**: Credentials stored in `st.session_state` and passed to bot pages
- **Authentication Guards**: Bot pages validate session state and redirect unauthorized access back to portal

### Google Sheet Setup

The portal integrates with a Google Sheet to manage student access codes. The sheet must have the following structure:

**Sheet ID**: `1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY`  
**Sheet Name**: `Sheet1`

**Required Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Table No | Student identifier or table number | 1, 2, 3... |
| Name | Student's full name | John Doe |
| Bot | Bot type assignment | OHI or HPV |
| Secret | Unique secret code | abc123xyz |
| Used | Whether code has been used | FALSE/TRUE |

### Service Account Setup

The portal uses a Google Cloud service account for authentication:

1. **Service Account File**: `umnsod-mibot-ea3154b145f1.json` (already included in repository)
2. **Required Permissions**: The service account email (`mibots@umnsod-mibot.iam.gserviceaccount.com`) must be granted **Editor** access to the Google Sheet
3. **Grant Access**: Share the Google Sheet with the service account email address

### Running the Portal

**Production (Multipage App):**
```bash
streamlit run secret_code_portal.py
```

The portal will:
1. Load access codes from the Google Sheet on startup (cached)
2. Prompt students for their name, Groq API key, and secret code
3. Validate the code and check if it's unused
4. Mark valid codes as used in the sheet (single-cell update for efficiency)
5. Store credentials in session state
6. Navigate internally to the assigned chatbot page (OHI or HPV)

**Note**: The bot pages (`pages/OHI.py` and `pages/HPV.py`) cannot be accessed directly. They check for valid session state and redirect unauthorized access back to the portal.

### Deployment Instructions

#### Local Testing
1. Ensure `umnsod-mibot-ea3154b145f1.json` is in the project directory
2. Verify the service account has access to the Google Sheet
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `streamlit run secret_code_portal.py`
5. Portal will start and bot pages will be accessible via internal navigation

#### Streamlit Cloud Deployment (Multipage App)
1. **Set Main File**: In Streamlit Cloud settings, set `secret_code_portal.py` as the main file
   
2. **Upload Service Account Credentials**:
   - Go to your Streamlit Cloud app settings → "Secrets" section
   - Add secret `GOOGLESA_B64` with base64-encoded service account JSON:
   ```bash
   # On your local machine, generate base64:
   cat umnsod-mibot-ea3154b145f1.json | base64 -w 0
   ```
   - Paste the output as the value for `GOOGLESA_B64` secret
   
   **Alternative**: Add as `GOOGLESA` (TOML table format) - see [GOOGLESA_QUICK_REFERENCE.md](GOOGLESA_QUICK_REFERENCE.md)

3. **Verify Multipage Structure**:
   - Ensure `pages/` directory with `OHI.py` and `HPV.py` is in your repository
   - Streamlit automatically recognizes these as app pages
   
4. **Deploy**:
   - Commit all changes to GitHub
   - Link repository to Streamlit Cloud
   - Deploy with `secret_code_portal.py` as the entrypoint
   - The app will support internal navigation between portal and bot pages

#### Important Notes for Production
- **Entry Point**: Always use `secret_code_portal.py` as the main entry
- **No Direct Bot Access**: Bot pages are protected by authentication guards
- **Session State**: Credentials are maintained across page navigation
- **Caching**: Google Sheets client and data are cached to reduce API calls
- **No External URLs**: Bot URLs are never exposed to students

#### Google Sheet Permissions
- Share the Google Sheet with: `mibots@umnsod-mibot.iam.gserviceaccount.com`
- Grant **Editor** permissions (required to mark codes as used)
- Verify access by testing code validation

### Managing Student Access

**Adding New Students**:
1. Open the Google Sheet
2. Add a new row with: Table No, Name, Bot (OHI/HPV), Secret (unique code), Used (FALSE)
3. Share the secret code with the student
4. Student uses the portal to access their assigned chatbot

**Resetting a Code**:
1. Find the student's row in the Google Sheet
2. Change the "Used" column from TRUE to FALSE
3. The code can now be used again

**Security Best Practices**:
- Generate unique, random secret codes for each student
- Use a password generator or random string generator
- Don't reuse codes across semesters
- Regularly audit the "Used" column to detect any issues


## Setup Instructions
To run this app on your own computer, follow these steps:

### Prerequisites
- Python installed on your machine (Python 3.10 recommended)
- Pip package manager installed
- A GROQ API key (get one from [Groq](https://docs.newo.ai/docs/groq-api-keys))
- (Optional) Gmail account with App Password for Box integration

### Installation

1. Clone or download the repository to your local machine:
   ```bash
   git clone https://github.com/manirathnam2001/ManiUMN-MI_chatbots.git
   cd ManiUMN-MI_chatbots
   ```

2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables Setup

For security, sensitive credentials should be stored in environment variables rather than in code or configuration files.

#### Option 1: Using .env file (Recommended for local development)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and fill in your actual credentials:
   ```bash
   # Required for chatbot functionality
   GROQ_API_KEY=your-actual-groq-api-key
   
   # Required for Box email integration (optional if not using Box upload)
   SMTP_USERNAME=your-email@umn.edu
   SMTP_APP_PASSWORD=your-gmail-app-password
   OHI_BOX_EMAIL=your-ohi-box-email@u.box.com
   HPV_BOX_EMAIL=your-hpv-box-email@u.box.com
   ```

3. **Important**: Never commit the `.env` file to version control. It's already in `.gitignore`.

#### Option 2: System Environment Variables (Recommended for production)

Set environment variables in your system or deployment platform:

**Linux/Mac:**
```bash
export GROQ_API_KEY="your-groq-api-key"
export SMTP_USERNAME="your-email@umn.edu"
export SMTP_APP_PASSWORD="your-app-password"
export OHI_BOX_EMAIL="your-ohi-box-email@u.box.com"
export HPV_BOX_EMAIL="your-hpv-box-email@u.box.com"
```

**Windows (Command Prompt):**
```cmd
set GROQ_API_KEY=your-groq-api-key
set SMTP_USERNAME=your-email@umn.edu
set SMTP_APP_PASSWORD=your-app-password
set OHI_BOX_EMAIL=your-ohi-box-email@u.box.com
set HPV_BOX_EMAIL=your-hpv-box-email@u.box.com
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY="your-groq-api-key"
$env:SMTP_USERNAME="your-email@umn.edu"
$env:SMTP_APP_PASSWORD="your-app-password"
$env:OHI_BOX_EMAIL="your-ohi-box-email@u.box.com"
$env:HPV_BOX_EMAIL="your-hpv-box-email@u.box.com"
```

#### Gmail App Password Setup (for Box Integration)

If you're using Gmail for Box integration:

1. Enable 2-factor authentication on your Google account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new App Password for "Mail"
4. Use this App Password (not your regular Gmail password) as `SMTP_APP_PASSWORD`

#### Verifying Your Configuration

Test your environment variables are set correctly:
```bash
python3 config_loader.py
```

This will show which environment variables are configured and which are missing.

### How to run it on your own machine

3. Run the multipage app:
   ```bash
   # Main entry point (recommended)
   streamlit run secret_code_portal.py
   ```
   
   This starts the complete multipage application with:
   - Portal at the main page
   - OHI and HPV bots accessible via internal navigation
   - Centralized authentication and credentials

   **Legacy standalone apps** (deprecated, for testing only):
   ```bash
   # For HPV chatbot standalone (bypasses portal)
   streamlit run HPV.py
   
   # For OHI chatbot standalone (bypasses portal)
   streamlit run OHI.py
   ```
   
   Note: Standalone apps require manual entry of API key and student name on each page.

### Security Notes

⚠️ **IMPORTANT SECURITY PRACTICES:**

- **Never commit credentials** to version control
- **Use environment variables** for all sensitive data
- **Rotate credentials regularly** (every 90 days recommended)
- **Use App Passwords** for Gmail instead of your account password
- **Keep .env file private** - it should never be shared or committed
- **Review .gitignore** to ensure sensitive files are excluded

### Troubleshooting

**"Missing environment variable" error:**
- Ensure your `.env` file exists and has the correct values
- Or verify system environment variables are set correctly
- Run `python3 config_loader.py` to check configuration status

**GROQ API key not working:**
- Verify the key is correct at [Groq Console](https://console.groq.com)
- Check that GROQ_API_KEY is set in environment variables
- Ensure there are no extra spaces or quotes around the key

**Email/Box integration not working:**
- Verify Gmail App Password is correct (16 characters without spaces)
- Ensure 2-factor authentication is enabled on your Gmail account
- Check that Box email addresses are correct
- Run `python3 email_utils.py` to test SMTP connection

**"Module not found" errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try upgrading pip: `pip install --upgrade pip`
- For Mac M1/M2 users with faiss-cpu issues, try: `conda install -c pytorch faiss-cpu`

**Streamlit app not loading or crashing:**
- Check Python version (3.10+ recommended)
- Clear Streamlit cache: `streamlit cache clear`
- Verify GROQ API key is valid and has available quota
- Check internet connection for API calls

**PDF generation fails:**
- Ensure student name is provided and doesn't contain special characters
- Check that conversation has at least a few exchanges
- Verify reportlab is installed correctly

**Conversation not ending or feedback button disabled:**
- Continue conversation for at least 8 turns (4 exchanges)
- Look for natural conversation ending cues
- Ensure conversation state hasn't encountered an error

For additional help, check the logs in the Streamlit console or run the test scripts:
- `python3 config_loader.py` - Test configuration
- `python3 email_utils.py` - Test email setup
- `python3 test_scoring_consistency.py` - Test scoring system
