# Quick Start Guide - Environment Variables Setup

## For New Users

### Step 1: Copy the example file
```bash
cp .env.example .env
```

### Step 2: Edit .env with your credentials
```bash
# Open .env in your text editor and fill in:
GROQ_API_KEY=your-actual-groq-api-key-here
SMTP_USERNAME=your-email@umn.edu
SMTP_APP_PASSWORD=your-gmail-app-password
```

### Step 3: Get Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and your device
3. Copy the generated password
4. Use it as SMTP_APP_PASSWORD in your .env file

### Step 4: Verify configuration
```bash
python3 config_loader.py
```

You should see ✅ for all required variables.

### Step 5: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 6: Run the app
```bash
streamlit run HPV.py
# or
streamlit run OHI.py
```

## Troubleshooting

### "Missing environment variables" error
**Solution:** Make sure your .env file exists and has all required variables set.

```bash
# Check if .env file exists
ls -la .env

# Verify configuration
python3 config_loader.py
```

### "GROQ API key not working"
**Solution:** 
1. Get a new key from https://console.groq.com
2. Make sure there are no extra spaces in your .env file
3. The key should look like: `gsk_...`

### "SMTP authentication failed"
**Solution:**
1. Make sure you're using an **App Password**, not your regular Gmail password
2. Enable 2-factor authentication on your Google account first
3. Generate a new App Password if needed

### Configuration not loading
**Solution:**
1. Make sure .env file is in the same directory as the Python files
2. Install python-dotenv: `pip install python-dotenv`
3. Check for syntax errors in .env (no quotes needed around values)

## Security Checklist

Before you start:
- [ ] Created .env file from .env.example
- [ ] Filled in all required credentials
- [ ] Generated Gmail App Password (not regular password)
- [ ] Verified .env is NOT committed to git (`git status` should not show .env)
- [ ] Tested configuration with `python3 config_loader.py`

## What NOT to Do

❌ **Don't** commit your .env file to git
❌ **Don't** share your .env file with others
❌ **Don't** use your regular Gmail password (use App Password)
❌ **Don't** put credentials in config.json
❌ **Don't** put credentials directly in Python files

## What TO Do

✅ **Do** use environment variables for all credentials
✅ **Do** keep your .env file private
✅ **Do** use Gmail App Passwords
✅ **Do** rotate credentials regularly (every 90 days)
✅ **Do** verify configuration before running

## For Production Deployment

Instead of .env file, set system environment variables:

**Linux/Mac:**
```bash
export GROQ_API_KEY="your-key"
export SMTP_USERNAME="your-email@umn.edu"
export SMTP_APP_PASSWORD="your-app-password"
```

**Windows PowerShell:**
```powershell
$env:GROQ_API_KEY="your-key"
$env:SMTP_USERNAME="your-email@umn.edu"
$env:SMTP_APP_PASSWORD="your-app-password"
```

**Docker:**
```dockerfile
ENV GROQ_API_KEY=your-key
ENV SMTP_USERNAME=your-email@umn.edu
ENV SMTP_APP_PASSWORD=your-app-password
```

## Need Help?

1. Run `python3 config_loader.py` to see what's missing
2. Check README.md for detailed instructions
3. Review SECURITY_CONFIG_IMPLEMENTATION.md for full documentation
4. Check the troubleshooting section above

## Quick Commands

```bash
# Verify configuration
python3 config_loader.py

# Test email functionality
python3 email_utils.py

# Run all tests
python3 test_config_loader.py
python3 test_email_utils.py

# Run the chatbot
streamlit run HPV.py
streamlit run OHI.py
```

---

**Remember:** Never commit credentials to git! Always use environment variables for sensitive data.
