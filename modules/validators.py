import re

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$")

def clean_str(s: str) -> str:
    return (s or "").strip()

def normalize_phone(phone: str) -> str:
    p = clean_str(phone)
    p = re.sub(r"[ \.\-()]", "", p)
    if p.startswith("+33"):
        p = "0" + p[3:]
    if p.startswith("0033"):
        p = "0" + p[4:]
    return p

def is_valid_phone_fr(phone: str) -> bool:
    p = normalize_phone(phone)
    return bool(re.fullmatch(r"0\d{9}", p))

def is_valid_email(email: str) -> bool:
    e = clean_str(email)
    if not e:
        return True
    return bool(EMAIL_REGEX.fullmatch(e))

def require(value: str, field_name: str) -> str:
    v = clean_str(value)
    if not v:
        raise ValueError(f"Le champ '{field_name}' est obligatoire.")
    return v
