import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def send_test_email(config):
    # Use email_config section as it has the complete credentials
    email_config = config['email_config']
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = email_config['smtp_username']
    msg['To'] = email_config['ohi_box_email']  # Using OHI box email as test
    msg['Subject'] = 'Test Email to Box'
    
    # Add body
    body = "This is a test email to Box integration."
    msg.attach(MIMEText(body, 'plain'))
    
    # Create a test file
    test_content = "This is a test file content"
    with open('test.txt', 'w') as f:
        f.write(test_content)
    
    # Attach the file
    with open('test.txt', 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='txt')
        attachment.add_header('Content-Disposition', 'attachment', filename='test.txt')
        msg.attach(attachment)
    
    # Connect to SMTP server
    server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
    server.starttls()
    server.login(email_config['smtp_username'], email_config['smtp_app_password'])
    
    # Send email
    server.send_message(msg)
    server.quit()
    
    # Clean up
    os.remove('test.txt')
    print("Test email sent successfully!")

if __name__ == "__main__":
    config = load_config()
    send_test_email(config)