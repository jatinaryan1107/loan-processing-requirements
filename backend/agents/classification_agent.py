"""Classify requirement type and quality attributes using explicit rules."""

import re

CATEGORIES = {
    "security": [
        "authentication",
        "authenticate",
        "password",
        "encrypt",
        "access",
        "login",
        "security",
        "role",
    ],
    "privacy": ["personal", "sensitive", "privacy", "minimis", "minimiz", "retention", "retain", "delete"],
    "compliance": ["regulat", "rbi", "kyc", "law", "compliance", "jurisdiction"],
    "performance": ["latency", "response time", "quick", "fast", "concurrent", "throughput"],
    "availability": ["uptime", "available", "availability", "recover", "backup"],
    "auditability": ["audit", "logging", "timestamp"],
    "integration": ["api", "legacy", "integrat", "disburs", "gateway"],
    "usability": ["user-friendly", "accessible", "usability", "screen reader"],
    "operational": ["maintain", "monitor", "incident", "exception", "retry"],
}


TIME_TARGET = re.compile(
    r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|ten|per)\s*(?:milliseconds?|seconds?|ms)\b"
)
AUTH_ACTION = re.compile(r"\b(?:shall|must|should)\s+(?:authenticate\b|require\s+authentication\b)")


def classify(text):
    lower = text.lower()
    categories = [
        cat
        for cat, terms in CATEGORIES.items()
        if any(re.search(r"\b" + re.escape(term), lower) for term in terms)
    ]
    if TIME_TARGET.search(lower) and "performance" not in categories:
        categories.append("performance")
    quality_attributes = {"performance", "availability", "usability", "privacy", "security"}
    if AUTH_ACTION.search(lower):
        quality_attributes.remove("security")
    kind = "non-functional" if quality_attributes.intersection(categories) else "functional"
    return kind, categories or ["business"]
