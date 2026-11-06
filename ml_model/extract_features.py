from urllib.parse import urlparse
import re


def extract_features(url):
    url = str(url).strip()

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "http://" + url

    parsed = urlparse(url)

    domain = parsed.netloc.lower()

    if "@" in domain:
        domain = domain.split("@")[-1]

    domain = domain.split(":")[0]

    if domain.startswith("www."):
        domain = domain[4:]

    path = parsed.path or ""

    # Same suspicious words used during model training
    suspicious_words = [
        "login", "signin", "verify", "verification",
        "secure", "account", "update", "confirm",
        "password", "credential", "wallet", "bank",
        "payment", "reward", "free", "bonus",
        "claim", "refund", "urgent", "otp", "kyc",
        "upi", "transaction"
    ]

    # Same shortened URL services used during training
    shortened_services = [
        "bit.ly", "tinyurl.com", "t.co", "goo.gl",
        "ow.ly", "is.gd", "buff.ly", "cutt.ly",
        "shorturl.at"
    ]

    features = {}

    # Basic URL features
    features["url_length"] = len(url)
    features["domain_length"] = len(domain)
    features["num_dots"] = url.count(".")
    features["num_hyphens"] = url.count("-")
    features["num_underscores"] = url.count("_")
    features["num_slashes"] = url.count("/")
    features["num_digits"] = sum(c.isdigit() for c in url)

    features["num_special_chars"] = sum(
        not c.isalnum() for c in url
    )

    # Security indicators
    features["has_https"] = int(
        parsed.scheme.lower() == "https"
    )

    features["has_ip"] = int(
        re.match(
            r"^\d{1,3}(\.\d{1,3}){3}$",
            domain
        ) is not None
    )

    features["has_at_symbol"] = int("@" in url)
    features["has_query"] = int(bool(parsed.query))
    features["has_fragment"] = int(bool(parsed.fragment))

    # Domain indicators
    domain_parts = [
        part for part in domain.split(".") if part
    ]

    features["subdomain_count"] = max(
        len(domain_parts) - 2, 0
    )

    url_lower = url.lower()

    features["suspicious_word_count"] = sum(
        1 for word in suspicious_words
        if word in url_lower
    )

    features["is_shortened"] = int(
        any(
            service in domain
            for service in shortened_services
        )
    )

    # Path feature
    features["path_length"] = len(path)

    # Ratios
    features["digit_ratio"] = (
        features["num_digits"] / max(len(url), 1)
    )

    features["special_ratio"] = (
        features["num_special_chars"] / max(len(url), 1)
    )

    return features 