"""
Utility functions for the reports app.
"""
import bleach

# Allowed HTML tags for rich text fields (PRD section 6.1)
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u',
    'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4',
    'blockquote', 'a', 'span'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target'],
    'span': ['class'],
}


def sanitize_html(value: str) -> str:
    """
    Strip disallowed HTML tags and attributes from rich text fields.
    Per PRD section 6.1: rich text output 'stored as sanitized HTML
    and sanitized server-side before persistence.'
    """
    if not value:
        return value
    return bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
        strip_comments=True
    )
