ef clean_text(text: str) -> str | None:
    """
    Collapse whitespace and strip leading/trailing spaces.
    Returns None if text is falsy.
    """
    if text:
        return " ".join(text.split()).strip()
    return None
