"""
Time utilities for consistent timezone handling across MI chatbot applications.

This module provides timezone conversion functions to ensure all timestamps
are displayed in the Minnesota timezone (America/Chicago) for consistency
across the OHI and HPV assessment applications.

Functions:
- get_formatted_utc_time(): Returns current time in Minnesota timezone
- convert_to_minnesota_time(): Converts UTC time strings to Minnesota timezone

All timestamps in the application use the format: 'YYYY-MM-DD HH:MM:SS'
"""

from datetime import datetime
import pytz

def get_formatted_utc_time():
    """Returns current time in Minnesota timezone (America/Chicago) in YYYY-MM-DD HH:MM:SS format"""
    minnesota_tz = pytz.timezone('America/Chicago')
    mn_time = datetime.now(minnesota_tz)
    return mn_time.strftime("%Y-%m-%d %H:%M:%S")

def convert_to_minnesota_time(utc_time_str: str) -> str:
    """Convert UTC time to Minnesota time with proper formatting.
    
    Args:
        utc_time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS' (may include timezone info)
        
    Returns:
        Minnesota time string in format 'YYYY-MM-DD HH:MM:SS AM/PM TZ'
    """
    try:
        # Parse UTC time without timezone info first
        # Handle both 'YYYY-MM-DD HH:MM:SS' and 'YYYY-MM-DD HH:MM:SS TZ' formats
        time_parts = utc_time_str.split()
        if len(time_parts) >= 2:
            # Has date and time (and possibly timezone)
            utc_dt = datetime.strptime(f"{time_parts[0]} {time_parts[1]}", '%Y-%m-%d %H:%M:%S')
        else:
            # Fallback to original format
            utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
        
        utc_dt = pytz.utc.localize(utc_dt)
        
        # Convert to Minnesota time
        mn_tz = pytz.timezone('America/Chicago')
        mn_time = utc_dt.astimezone(mn_tz)
        
        # Format with AM/PM and timezone
        return mn_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')
    except Exception as e:
        print(f"Time conversion error: {e}")
        return utc_time_str  # Fallback to original time
