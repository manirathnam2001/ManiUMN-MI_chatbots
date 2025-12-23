"""
Time utilities for consistent timezone handling across MI chatbot applications.

This module provides timezone conversion functions to ensure all timestamps
are displayed in CST (America/Chicago timezone) for consistency across all
MI assessment applications.

Functions:
- get_cst_timestamp(): Returns current time in CST with timezone indicator
- get_cst_datetime(): Returns datetime object in CST timezone
- convert_to_minnesota_time(): Converts UTC time strings to CST with indicator
- get_formatted_utc_time(): Alias for backward compatibility

All timestamps include timezone indicator (CST or CDT) for clarity.
"""

from datetime import datetime
import pytz


def get_cst_timestamp() -> str:
    """Returns current time in CST (America/Chicago) with timezone indicator.
    
    Returns:
        Timestamp string in format 'YYYY-MM-DD HH:MM:SS AM/PM CST'
        Example: '2025-12-23 02:30:45 PM CST' or '2025-06-15 03:45:12 PM CDT'
    """
    cst_tz = pytz.timezone('America/Chicago')
    cst_time = datetime.now(cst_tz)
    formatted_time = cst_time.strftime('%Y-%m-%d %I:%M:%S %p')
    tz_abbr = cst_time.strftime('%Z')  # CST or CDT depending on daylight saving
    return f"{formatted_time} {tz_abbr}"


def get_cst_datetime():
    """Returns current datetime object in CST timezone.
    
    Returns:
        datetime: Timezone-aware datetime object in America/Chicago timezone
    """
    cst_tz = pytz.timezone('America/Chicago')
    return datetime.now(cst_tz)


def get_cst_for_pdf() -> str:
    """
    Get CST timestamp formatted for PDF metadata.
    
    Returns:
        String in PDF date format with CST offset, e.g., 'D:20251223173045-06'00''
    """
    cst_tz = pytz.timezone('America/Chicago')
    now_cst = datetime.now(cst_tz)
    # PDF date format: D:YYYYMMDDHHmmss+HH'mm'
    offset = now_cst.strftime('%z')  # e.g., '-0600' or '-0500'
    offset_formatted = f"{offset[:3]}'{offset[3:]}'"  # Convert to -06'00' or -05'00'
    return f"D:{now_cst.strftime('%Y%m%d%H%M%S')}{offset_formatted}"


# CST Timezone constant
CST_TIMEZONE = pytz.timezone('America/Chicago')


# Backward compatibility alias
def get_formatted_utc_time():
    """Returns current time in CST timezone (America/Chicago).
    
    Note: Despite the function name (kept for backward compatibility),
    this returns CST time with timezone indicator.
    
    Returns:
        Timestamp string in format 'YYYY-MM-DD HH:MM:SS AM/PM CST'
    """
    return get_cst_timestamp()


def get_current_utc_time():
    """Returns current time in UTC timezone in YYYY-MM-DD HH:MM:SS format"""
    utc_time = datetime.now(pytz.UTC)
    return utc_time.strftime("%Y-%m-%d %H:%M:%S")


def convert_to_minnesota_time(utc_time_str):
    """Convert UTC time string to CST timezone with AM/PM and timezone abbreviation.
    
    Args:
        utc_time_str: UTC time string in format 'YYYY-MM-DD HH:MM:SS'
        
    Returns:
        CST time string in format 'YYYY-MM-DD HH:MM:SS AM/PM TIMEZONE'
        Example: '2025-10-07 10:50:21 PM CDT' or '2025-12-23 02:30:45 PM CST'
    """
    cst_tz = pytz.timezone('America/Chicago')
    utc_dt = datetime.strptime(utc_time_str, '%Y-%m-%d %H:%M:%S')
    utc_dt = pytz.utc.localize(utc_dt)
    cst_time = utc_dt.astimezone(cst_tz)
    # Format with AM/PM and timezone abbreviation
    formatted_time = cst_time.strftime('%Y-%m-%d %I:%M:%S %p')
    tz_abbr = cst_time.strftime('%Z')
    return f"{formatted_time} {tz_abbr}"
