import bleach
import re

ALLOWED_TAGS=[
    "p","h1","h2","ul","ol","li","sub","sup","blockquote",
    "pre","a","img","span","strong","em","u","s","br"
]


ALLOWED_ATTRIBUTES={"a": ["href","title"]}

ALLOWED_SCHEMES=["http","https"]


def sanitize_string(string):
    if string is None:
        return ""
    
    cleaned_string = bleach.clean(string, tags=[], strip=True)
    
    pattern = re.compile(r"[^a-zA-Z0-9\s',:.?-ÁÉÍÓÚáéíóú]")
    
    
    sanitize_string = pattern.sub("", cleaned_string)
    
    return sanitize_string

def sanitize_html(content):
    if content is None:
        return ""
    
    return bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_SCHEMES,
        strip=True
    )