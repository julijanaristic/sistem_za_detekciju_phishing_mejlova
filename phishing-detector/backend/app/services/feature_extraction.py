import re
from urllib.parse import urlparse

import tldextract
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from app.models.schemas import UrlFinding

from app.core.legitimate_domains import LEGITIMATE_SENDER_DOMAINS

URL_REGEX = re.compile(r"https?://[^\s\"'<>]+")

# TODO: expand this list
KNOWN_BRANDS = [
    "paypal", "google", "microsoft", "apple", "amazon", "facebook", "netflix", "instagram", "linkedin"
]

def extract_urls(text: str) -> list[str]:
    urls = set(URL_REGEX.findall(text))

    try:
        soup = BeautifulSoup(text, "lxml")
        for a in soup.find_all("a", href=True):
            urls.add(a["href"])
        
    except Exception:
        pass
    
    return list(urls)

def analyze_url(url: str) -> UrlFinding:
    # TODO: add checking if the domain is younger than X days, check against a list of known URL shorteners, check wheteher the domain is on a public phishing blocklist
    try:
        parsed = urlparse(url)
        ext = tldextract.extract(url)
        domain=f"{ext.domain}.{ext.suffix}"
    except Exception:
        return UrlFinding(url=url, is_suspicious=True, reason="Incorrect URL format")
    
    ip_pattern = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
    if ip_pattern.match(parsed.hostname or ""):
        return UrlFinding(url=url, is_suspicious=True, reason="Uses IP address instead of domain")
    
    if parsed.scheme != "https":
        return UrlFinding(url=url, is_suspicious=True, reason="Does not use HTTPS")
    
    for brand in KNOWN_BRANDS:
        similarity = fuzz.ratio(ext.domain.lower(), brand)
        if brand not in ext.domain.lower() and similarity > 70:
            return UrlFinding(
                url=url, is_suspicious=True,
                reason=f"Domain mimics brand '{brand}' but it is not official ({domain})"
            )
    
    if ext.subdomain.count(".") >= 2:
        return UrlFinding(url=url, is_suspicious=True, reason="Too many subdomains")
    
    return UrlFinding(url=url, is_suspicious=False, reason=None)

def analyze_urls_in_text(text: str) -> list[UrlFinding]:
    return [analyze_url(u) for u in extract_urls(text)]

def sender_mismatch(display_name: str | None, sender_email: str | None) -> bool:
    if not display_name or not sender_email or "@" not in sender_email:
        return False
    
    domain = sender_email.split("@")[-1].lower()
    name_tokens = re.findall(r"[a-zA-z]+", display_name.lower())
    return not any(token in domain for token in name_tokens if len(token) > 3)

def is_legitimate_sender(sender: str | None) -> bool:
    if not sender or "@" not in sender:
        return False

    email_match = re.search(
        r"<([^<>@\s]+@[^<>@\s]+)>",
        sender,
    )

    email = (
        email_match.group(1)
        if email_match
        else sender.strip()
    )

    if "@" not in email:
        return False

    domain = email.split("@")[-1].lower().strip()

    return domain in LEGITIMATE_SENDER_DOMAINS