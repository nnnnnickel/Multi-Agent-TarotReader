import re


CARD_ORIENTATION_PATTERN = re.compile(
    r"^(?P<name>.+?)(?:\s*[-,/]?\s+|\s*[-,/]?\s*)"
    r"(?P<orientation>reversed|reverse|rev|upright|逆位|正位)\s*$",
    flags=re.IGNORECASE,
)


def standardize_card_input(card):
    """Normalize one user card name while preserving upright/reversed markers."""
    cleaned = " ".join(str(card).strip().split())
    if not cleaned:
        return ""
    if re.search(r"\((reversed|upright|逆位|正位)\)$", cleaned, flags=re.IGNORECASE):
        return cleaned
    match = CARD_ORIENTATION_PATTERN.match(cleaned)
    if not match:
        return cleaned
    name = match.group("name").strip(" -,/")
    orientation = match.group("orientation").lower()
    if not name:
        return cleaned
    if orientation in {"reversed", "reverse", "rev", "逆位"}:
        return f"{name} (reversed)"
    return f"{name} (upright)"


def standardize_card_inputs(cards):
    """Normalize a list of card names and remove empty values."""
    return [card for card in (standardize_card_input(item) for item in cards) if card]
