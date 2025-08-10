"""
Utility functions for Court Data Fetcher application
"""

import os
import re
import logging
from datetime import datetime

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def validate_case_number(case_number):
    """
    Validate case number format
    
    Args:
        case_number (str): Case number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not case_number or not isinstance(case_number, str):
        return False
    
    # Remove whitespace
    case_number = case_number.strip()
    
    # Check basic format (numbers and common separators)
    pattern = r'^[0-9]+[\/\-]?[0-9]*$'
    
    if not re.match(pattern, case_number):
        return False
    
    # Check length constraints
    if len(case_number) < 1 or len(case_number) > 50:
        return False
    
    return True

def sanitize_filename(filename):
    """
    Sanitize filename for safe file system storage
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename:
        return 'unknown'
    
    # Remove or replace problematic characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores and whitespace
    filename = filename.strip('_ ')
    
    # Ensure filename is not empty
    if not filename:
        filename = f'file_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def validate_filing_year(year):
    """
    Validate filing year
    
    Args:
        year: Year to validate (can be string or int)
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        year_int = int(year)
        current_year = datetime.now().year
        
        # Check reasonable year range (courts established in 1950s)
        if 1950 <= year_int <= current_year:
            return True
        else:
            return False
            
    except (ValueError, TypeError):
        return False

def format_date_for_display(date_str):
    """
    Format date string for display
    
    Args:
        date_str (str): Date string in ISO format (YYYY-MM-DD)
        
    Returns:
        str: Formatted date string
    """
    if not date_str:
        return 'Not available'
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%d %B %Y')
    except ValueError:
        return date_str

def truncate_text(text, max_length=100):
    """
    Truncate text to specified length with ellipsis
    
    Args:
        text (str): Text to truncate
        max_length (int): Maximum length
        
    Returns:
        str: Truncated text
    """
    if not text:
        return ''
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + '...'

def get_case_types():
    """
    Get list of available case types
    
    Returns:
        list: List of case types
    """
    return [
        'Civil Appeal',
        'Criminal Appeal',
        'Civil Writ Petition',
        'Criminal Writ Petition',
        'Company Appeal',
        'Tax Appeal',
        'Service Matter',
        'Arbitration Petition',
        'Contempt Petition',
        'Execution Petition',
        'Regular Civil Suit',
        'Summary Civil Suit',
        'Miscellaneous Application',
        'Criminal Revision',
        'Criminal Misc.',
        'Bail Application'
    ]

def get_filing_years():
    """
    Get list of available filing years
    
    Returns:
        list: List of years from 2000 to current year
    """
    current_year = datetime.now().year
    return list(range(current_year, 1999, -1))  # Descending order

def extract_case_number_parts(case_number):
    """
    Extract components from case number
    
    Args:
        case_number (str): Case number like "123/2023" or "456-2022"
        
    Returns:
        dict: Dictionary with 'number' and 'year' keys
    """
    if not case_number:
        return {'number': '', 'year': ''}
    
    # Try to extract number and year
    parts = re.split(r'[\/\-]', case_number.strip())
    
    if len(parts) >= 2:
        return {
            'number': parts[0].strip(),
            'year': parts[1].strip()
        }
    else:
        return {
            'number': case_number.strip(),
            'year': ''
        }

def generate_search_id():
    """
    Generate unique search ID for logging
    
    Returns:
        str: Unique search identifier
    """
    return f"search_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

def is_valid_url(url):
    """
    Check if URL is valid
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL
    """
    if not url:
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def clean_html_text(html_text):
    """
    Clean HTML text by removing tags and extra whitespace
    
    Args:
        html_text (str): HTML text to clean
        
    Returns:
        str: Cleaned text
    """
    if not html_text:
        return ''
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_text)
    
    # Replace HTML entities
    clean_text = clean_text.replace('&nbsp;', ' ')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = clean_text.strip()
    
    return clean_text

def get_file_size_string(size_bytes):
    """
    Convert file size in bytes to human readable string
    
    Args:
        size_bytes (int): File size in bytes
        
    Returns:
        str: Human readable file size
    """
    if size_bytes == 0:
        return '0 B'
    
    size_names = ['B', 'KB', 'MB', 'GB']
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f'{s} {size_names[i]}'

def create_backup_filename(original_path):
    """
    Create backup filename with timestamp
    
    Args:
        original_path (str): Original file path
        
    Returns:
        str: Backup file path
    """
    if not original_path:
        return None
    
    base_name = os.path.splitext(original_path)[0]
    extension = os.path.splitext(original_path)[1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    return f"{base_name}_backup_{timestamp}{extension}"