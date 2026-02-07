import re

# Professional-grade basic blacklist for 2026
_BLOCK_PATTERNS = [
    r"\b(nud(e|ity)|porn|explicit|sex(ual)?|hardcore|nsfw)\b",
    r"\b(child|minor|underage)\b",
    r"\b(gore|blood|violence|killing|death)\b",
    # r"\b(bomb|weapon|illegal|drug)\b",
]


def is_prompt_allowed(prompt: str) -> tuple[bool, str]:
    """
    Returns (True, "") if safe, (False, reason) if blocked.
    Using word boundaries (\b) prevents blocking 'wholesale' or 'knight'.
    """
    p = prompt.lower().strip()
    if not p:
        return False, "Prompt is empty."

    for pat in _BLOCK_PATTERNS:
        if re.search(pat, p):
            return False, f"🚫 Safety Block: Your request contains restricted terms ({pat})."

    return True, ""
