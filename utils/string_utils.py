import bleach
import re

def sanitize_string(string):
    if string is None:
        return ""
    
    cleaned_string = bleach.clean(string, tags=[], strip=True)
    
    pattern = re.compile(r"[^a-zA-Z0-9\s',:.?-ÁÉÍÓÚáéíóú]")
    
    
    sanitize_string = pattern.sub("", cleaned_string)
    
    return sanitize_string
    