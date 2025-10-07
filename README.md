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

### Installation
1. Clone or download the repository to your local machine:
   ```bash
   git clone https://github.com/anwesha-umn/MI_chatbots.git
   cd MI_chatbots
   ```

### How to run it on your own machine

2. Install the requirements 

   ```bash
   $ pip install -r requirements.txt
   ```

3. Run the app on local machine 

   ```bash
   $ streamlit run HPV.py
   ```

---

## 📧 Email Configuration (For Box Upload Feature)

The application can automatically upload PDF reports to Box via email. To enable this feature, you need to configure SMTP settings.

### SMTP Configuration

The SMTP settings are configured in `config.json` under the `email_config` section:

```json
{
  "email_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_ssl": true,
    "smtp_user": "your-email@umn.edu",
    "smtp_password": "PLACEHOLDER",
    "ohi_box_email": "OHI_dir.zcdwwmukjr9ab546@u.box.com",
    "hpv_box_email": "HPV_Dir.yqz3brxlhcurhp2l@u.box.com"
  }
}
```

### Setting Up Environment Variables

**For security reasons, SMTP passwords should never be stored in config files.** Instead, use environment variables:

#### On Linux/Mac:
```bash
export SMTP_PASSWORD="your-app-password"
```

To make it permanent, add it to your `~/.bashrc` or `~/.bash_profile`:
```bash
echo 'export SMTP_PASSWORD="your-app-password"' >> ~/.bashrc
source ~/.bashrc
```

#### On Windows (Command Prompt):
```cmd
set SMTP_PASSWORD=your-app-password
```

#### On Windows (PowerShell):
```powershell
$env:SMTP_PASSWORD="your-app-password"
```

To make it permanent on Windows, add it as a system environment variable:
1. Search for "Environment Variables" in Windows settings
2. Click "New" under User variables
3. Variable name: `SMTP_PASSWORD`
4. Variable value: Your app password

### Gmail App Password Setup

If using Gmail, you need to create an App Password:

1. **Enable 2-Factor Authentication** on your Google account
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification

2. **Generate an App Password**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Enter "MI Chatbots" as the name
   - Click "Generate"
   - Copy the 16-character password

3. **Set the environment variable** with the generated App Password
   ```bash
   export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
   ```

### Testing Email Configuration

Test your email configuration:

```bash
python3 email_config.py
```

This will verify:
- Configuration file loads correctly
- Box email addresses are configured
- Environment variable is set
- SMTP connection works

### Enabling Box Upload

To enable automatic Box uploads:

1. Set up email configuration (above)
2. Edit `config.json` and set `box_upload.enabled` to `true`:
   ```json
   {
     "box_upload": {
       "enabled": true
     }
   }
   ```

### Security Best Practices

- ✅ **DO** use environment variables for passwords
- ✅ **DO** use Gmail App Passwords (not your main password)
- ✅ **DO** keep `config.json` with placeholder values in version control
- ❌ **DON'T** commit real passwords to version control
- ❌ **DON'T** share your App Password with others
- ❌ **DON'T** use your main email password
