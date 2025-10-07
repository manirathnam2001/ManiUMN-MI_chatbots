# MI Chatbots

This repository contains two Motivational Interviewing (MI) chatbot applications built using Streamlit:

- `HPV.py`: Practice MI skills related to **HPV vaccine**  
- `OHI.py`: Practice MI skills for **Oral Hygiene**

These chatbots simulate realistic patient interactions and provide **automated MI feedback** based on example transcripts stored in `*.txt` format.
We use **Groq LLMs** for real-time dialogue and **retrieval-augmented generation (RAG)** to incorporate structured feedback from rubric documents.

---
## 📁 Project Structure

    anwesha-umn/
    ├── .devcontainer/         # Dev Container setup (for VS Code Remote/Containers)
    ├── hpv_rubrics/           # HPV MI example transcripts + rubric feedback (.txt format)
    ├── ohi_rubrics/           # Oral Hygiene MI transcripts + rubric feedback (.txt format)
    ├── HPV.py                 # Streamlit app for HPV vaccine MI chatbot
    ├── OHI.py                 # Streamlit app for Oral Health MI chatbot
    ├── README.md              # Instructions to set up and run the app
    ├── requirements.txt       # Python dependencies for the chatbot
    └── runtime.txt            # (Optional) Python version for deployment environments (e.g., Streamlit Cloud)

> You can add more `.txt` transcripts with MI feedback in the `hpv_rubrics/` or `ohi_rubrics/` folders to improve the RAG-based evaluation.

---

## 🧬 HPV MI Practice App

This app simulates a realistic patient interaction to practice Motivational Interviewing (MI) skills for HPV vaccination discussions. Users can play the role of a patient or provider to engage in a conversation that focuses on exploring thoughts and feelings about the HPV vaccine.


Checkout the app here : [![Open HPV MI chatbot in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://hpvmiapp.streamlit.app/)


## 🦷 OHI MI Practice App
This app simulates a realistic dental hygiene patient interaction to help users—particularly dental students—practice **Motivational Interviewing (MI)** skills related to **oral hygiene and behavior change**.

The patient (played by AI) begins with scenarios (e.g., "I’ve noticed these yellow spots...") and reacts naturally to the student’s MI techniques. At the end of the session, the system evaluates the student's performance using an MI rubric and provides detailed, constructive feedback.

Checkout the app here : [![Open OHI MI Chatbot in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ohimiapp.streamlit.app/)


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

3. Run the app on local machine:
   ```bash
   # For HPV chatbot
   streamlit run HPV.py
   
   # For OHI chatbot
   streamlit run OHI.py
   ```

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

**GROQ API key not working:**
- Verify the key is correct at [Groq Console](https://console.groq.com)
- Check that GROQ_API_KEY is set in environment variables

**Email/Box integration not working:**
- Verify Gmail App Password is correct
- Ensure 2-factor authentication is enabled on your Gmail account
- Check that Box email addresses are correct
- Run `python3 config_loader.py` to verify configuration
