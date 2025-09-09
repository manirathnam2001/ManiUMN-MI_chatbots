from flask import Flask, request, render_template, redirect, url_for, session, flash
import os
from auth_utils import verify_code

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Path to the CSV file
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secret_codes.csv')

@app.route('/', methods=['GET', 'POST'])
def login():
    """Login page with authentication form"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        bot = request.form.get('bot', '').strip()
        
        # Validate form inputs
        if not name or not code or not bot:
            return render_template('login.html', 
                                 message='All fields are required.', 
                                 success=False)
        
        # Validate bot selection
        if bot not in ['HPV', 'OHI']:
            return render_template('login.html', 
                                 message='Invalid chatbot selection.', 
                                 success=False)
        
        # Verify the code
        if verify_code(name, code, bot, CSV_PATH):
            # Store login state in session
            session['authenticated'] = True
            session['name'] = name
            session['bot'] = bot
            session['code'] = code
            
            # Redirect to appropriate chatbot
            if bot == 'HPV':
                return redirect(url_for('hpv_chatbot'))
            else:
                return redirect(url_for('ohi_chatbot'))
        else:
            return render_template('login.html', 
                                 message='Invalid credentials or code already used.', 
                                 success=False)
    
    return render_template('login.html')

@app.route('/hpv')
def hpv_chatbot():
    """HPV chatbot route - requires authentication"""
    if not session.get('authenticated') or session.get('bot') != 'HPV':
        flash('Please log in to access the HPV chatbot.')
        return redirect(url_for('login'))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HPV Chatbot</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .welcome {{
                color: #333;
                margin-bottom: 20px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }}
            .logout-btn {{
                background-color: #dc3545;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }}
            .logout-btn:hover {{
                background-color: #c82333;
                text-decoration: none;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧬 HPV Chatbot</h1>
            <div class="welcome">
                <h2>Welcome, {session['name']}!</h2>
                <p>You have successfully accessed the HPV Motivational Interviewing chatbot.</p>
            </div>
            
            <div class="info">
                <h3>HPV Chatbot Features:</h3>
                <ul style="text-align: left; display: inline-block;">
                    <li>Practice motivational interviewing skills with HPV vaccine scenarios</li>
                    <li>Multiple patient personas (Alex, Bob, Charlie, Diana)</li>
                    <li>Real-time feedback based on MI rubric</li>
                    <li>PDF report generation with scoring</li>
                </ul>
            </div>
            
            <div class="info">
                <p><strong>Note:</strong> This is a stub implementation. In production, this would integrate 
                with the existing HPV.py Streamlit application or provide embedded access to the chatbot functionality.</p>
            </div>
            
            <a href="{url_for('logout')}" class="logout-btn">Logout</a>
        </div>
    </body>
    </html>
    """

@app.route('/ohi')
def ohi_chatbot():
    """OHI chatbot route - requires authentication"""
    if not session.get('authenticated') or session.get('bot') != 'OHI':
        flash('Please log in to access the OHI chatbot.')
        return redirect(url_for('login'))
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OHI Chatbot</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .welcome {{
                color: #333;
                margin-bottom: 20px;
            }}
            .info {{
                background-color: #e3f2fd;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #2196f3;
            }}
            .logout-btn {{
                background-color: #dc3545;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }}
            .logout-btn:hover {{
                background-color: #c82333;
                text-decoration: none;
                color: white;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦷 OHI Chatbot</h1>
            <div class="welcome">
                <h2>Welcome, {session['name']}!</h2>
                <p>You have successfully accessed the OHI (Oral Hygiene Instructions) chatbot.</p>
            </div>
            
            <div class="info">
                <h3>OHI Chatbot Features:</h3>
                <ul style="text-align: left; display: inline-block;">
                    <li>Practice motivational interviewing skills with oral hygiene scenarios</li>
                    <li>Multiple patient personas (Alex, Bob, Charles, Diana)</li>
                    <li>Real-time feedback based on MI rubric</li>
                    <li>PDF report generation with scoring</li>
                </ul>
            </div>
            
            <div class="info">
                <p><strong>Note:</strong> This is a stub implementation. In production, this would integrate 
                with the existing OHI.py Streamlit application or provide embedded access to the chatbot functionality.</p>
            </div>
            
            <a href="{url_for('logout')}" class="logout-btn">Logout</a>
        </div>
    </body>
    </html>
    """

@app.route('/logout')
def logout():
    """Logout route - clears session"""
    session.clear()
    return render_template('login.html', 
                         message='You have been logged out successfully.', 
                         success=True)

if __name__ == '__main__':
    # Make sure the CSV file exists
    if not os.path.exists(CSV_PATH):
        print(f"Warning: CSV file not found at {CSV_PATH}")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)