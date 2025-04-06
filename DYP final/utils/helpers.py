import re

def extract_mermaid_code(text: str) -> str | None:
    """Extracts Mermaid code from a Markdown code block."""
    if not isinstance(text, str):
        return None  # Handle non-string input
    # Case-insensitive search for ```mermaid ... ```
    match = re.search(r"```mermaid\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        # Return the content inside the fences, stripped of leading/trailing whitespace
        return match.group(1).strip()
    return None