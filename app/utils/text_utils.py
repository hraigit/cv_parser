"""Text utility functions."""
import re
from typing import Optional


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def extract_emails(text: str) -> list:
    """Extract email addresses from text.
    
    Args:
        text: Input text
        
    Returns:
        List of email addresses
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> list:
    """Extract phone numbers from text.
    
    Args:
        text: Input text
        
    Returns:
        List of phone numbers
    """
    # Basic phone number pattern (can be enhanced)
    phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
    return re.findall(phone_pattern, text)


def detect_language(text: str) -> Optional[str]:
    """Detect language from text (basic implementation).
    
    Args:
        text: Input text
        
    Returns:
        Language code ('tr', 'en', or None)
    """
    # Basic Turkish character detection
    turkish_chars = set('çğıöşüÇĞİÖŞÜ')
    
    if any(char in turkish_chars for char in text):
        return 'tr'
    
    # Default to English if no Turkish characters
    if any(char.isalpha() for char in text):
        return 'en'
    
    return None


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove special characters except dots, dashes, underscores
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    max_length = 255
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        name = name[:max_length - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    
    return filename


def count_words(text: str) -> int:
    """Count words in text.
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    return len(text.split())


def extract_urls(text: str) -> list:
    """Extract URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        List of URLs
    """
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)