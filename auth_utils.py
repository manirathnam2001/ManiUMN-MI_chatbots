import csv
import threading
import os

# Thread-safe lock for CSV operations
_lock = threading.Lock()

def verify_code(name, code, bot, csv_path):
    """
    Thread-safe function to verify and mark secret codes as used.
    
    Args:
        name (str): Student name
        code (str): Secret code
        bot (str): Bot type (HPV or OHI)
        csv_path (str): Path to the CSV file
        
    Returns:
        bool: True if authenticated and code marked as used, False otherwise
    """
    with _lock:
        # Check if CSV file exists
        if not os.path.exists(csv_path):
            return False
            
        # Read the CSV file
        rows = []
        found_match = False
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Check for matching unused code, name, and bot
                    if (row['code'] == code and 
                        row['name'] == name and 
                        row['bot'] == bot and 
                        row['used'].lower() == 'false'):
                        # Mark as used
                        row['used'] = 'True'
                        found_match = True
                    rows.append(row)
        except (IOError, csv.Error):
            return False
            
        # Write back to CSV if we found a match
        if found_match:
            try:
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['code', 'name', 'bot', 'used']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                return True
            except (IOError, csv.Error):
                return False
                
        return False