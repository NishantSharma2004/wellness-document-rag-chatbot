import re

def sanitize_input(text: str) -> str:
    """Sanitize user input against basic markup injection."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r'<[^>]*>', '', text)
    return cleaned.strip()

def sanitize_output(text: str) -> str:
    """Ensure output doesn't contain obvious sensitive data leak patterns (e.g. gsk_ API keys)."""
    # Mask Groq API keys if somehow leaked
    masked = re.sub(r'gsk_[a-zA-Z0-9]{40,}', '[MASKED_KEY]', text)
    return masked
