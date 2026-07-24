import re
from typing import Any
from urllib.parse import urlparse

# Keywords for detecting hiring intent
HIRING_INTENT_PATTERNS = [
    r"\bwe are hiring\b",
    r"\bwe're hiring\b",
    r"\bhiring\b",
    r"\blooking for\b",
    r"\bwe're looking for\b",
    r"\bopen position(s)?\b",
    r"\bjob opening(s)?\b",
    r"\bvacancy\b",
    r"\brecruitment\b",
    r"\bjoin our team\b",
    r"\bimmediate opening\b",
    r"\bmultiple openings\b",
    r"\bhiring alert\b",
    r"\binternship opportunity\b",
    r"\binternship opening\b",
    r"\bfresher hiring\b",
    r"\bexperienced professionals\b",
    r"\bcareer opportunity\b",
    r"\bjob opportunity\b",
]

# Keywords for application intent
APPLICATION_INTENT_PATTERNS = [
    r"\bsend your resume\b",
    r"\bsend your cv\b",
    r"\bshare your resume\b",
    r"\bapply here\b",
    r"\bapply now\b",
    r"\bapply using the link\b",
    r"\bemail your resume\b",
    r"\bemail your cv\b",
    r"\bdm me\b",
    r"\bmessage me\b",
    r"\breach out to me\b",
    r"\bfill the form\b",
    r"\bregister here\b",
    r"\bcomment below\b",
    r"\bdrop a comment\b",
    r"\bdrop interested\b",
    r"\bin the comments\b",
    r"\bcomment down below\b",
    r"\bcomment interested\b",
]

# Common roles for role detection (simplified)
ROLE_PATTERNS = [
    r"\bdeveloper\b",
    r"\bengineer\b",
    r"\banalyst\b",
    r"\bmanager\b",
    r"\bdesigner\b",
    r"\bintern\b",
    r"\barchitect\b",
    r"\bconsultant\b",
]

# Role categories for classifying extracted role
ROLE_CATEGORIES = {
    "engineering": ["developer", "engineer", "sde", "software", "backend", "frontend", "fullstack", "full-stack", "devops", "data", "ml", "ai", "machine learning", "deep learning", "cloud", "infrastructure", "site reliability", "systems", "platform"],
    "design": ["designer", "ux", "ui", "product designer", "graphic", "visual", "creative", "art"],
    "product": ["product manager", "pm", "product owner", "technical product manager"],
    "marketing": ["marketing", "growth", "seo", "content", "social media", "brand", "digital marketing"],
    "sales": ["sales", "account executive", "business development", "bd", "sales development", "sdr", "account manager"],
    "finance": ["finance", "accountant", "controller", "auditor", "financial analyst", "cfa"],
    "hr": ["hr", "human resources", "recruiter", "talent acquisition", "people operations", "people partner"],
    "operations": ["operations", "ops", "operations manager", "project manager", "program manager", "scrum master"],
    "legal": ["legal", "lawyer", "attorney", "paralegal", "compliance", "counsel"],
    "consulting": ["consultant", "strategy", "management consultant", "analyst"],
    "leadership": ["vp", "vice president", "director", "head of", "chief", "cto", "ceo", "coo", "cfo"],
}

# Hashtag pattern
HASHTAG_PATTERN = r"#(\w+)"


def _detect_role_category(role_text: str) -> str | None:
    """Detect role category from extracted role text."""
    if not role_text or role_text == "Unknown Role":
        return None
    role_lower = role_text.lower()
    for category, keywords in ROLE_CATEGORIES.items():
        for keyword in keywords:
            if keyword in role_lower:
                return category.upper()
    return None


def _calculate_confidence(hiring_intent: bool, role_detected: bool, has_application_methods: bool, has_email: bool, has_url: bool) -> float:
    """
    Calculate hiring confidence as a numeric score 0.0-1.0.

    Weights:
    - Hiring intent detected: +0.4
    - Role detected: +0.2
    - Application method found: +0.2
    - Email found: +0.1
    - URL found: +0.1
    """
    score = 0.0
    if hiring_intent:
        score += 0.4
    if role_detected:
        score += 0.2
    if has_application_methods:
        score += 0.2
    if has_email:
        score += 0.1
    if has_url:
        score += 0.1
    return round(min(score, 1.0), 2)


def _confidence_level(score: float) -> str:
    """Convert numeric 0.0-1.0 score to categorical label."""
    if score >= 0.7:
        return "HIGH"
    elif score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def parse_post(post_text: str) -> dict[str, Any]:
    """
    Parses a LinkedIn post to determine if it is a HIRING_POST and extracts relevant metadata.

    Returns numeric 0.0-1.0 confidence score (hiring_confidence_score).
    Also returns categorical confidence label for backward compatibility.
    Only uses real data from post text. No fabricated values.
    """
    if not post_text:
        return {"is_hiring_post": False, "confidence": "LOW", "hiring_confidence_score": 0.0}

    text_lower = post_text.lower()

    # 1. Detect Hiring Intent
    hiring_intent = any(re.search(pattern, text_lower) for pattern in HIRING_INTENT_PATTERNS)

    # Check for false positives
    false_positives = [
        "congratulations to our team",
        "we launched a new product"
    ]
    if any(fp in text_lower for fp in false_positives):
        if not hiring_intent or (hiring_intent and "we are hiring" not in text_lower):
            hiring_intent = False

    if not hiring_intent:
        return {"is_hiring_post": False, "confidence": "LOW", "hiring_confidence_score": 0.0}

    # 2. Extract Hashtags
    hashtags = re.findall(HASHTAG_PATTERN, post_text)
    hashtags = list(dict.fromkeys(hashtags))  # Deduplicate preserving order

    # 3. Extract Application Methods
    application_methods = []
    application_email = None
    application_emails = []
    application_url = None
    application_urls = []
    application_platform = None
    application_form_url = None
    application_url_type = None

    # Extract all Emails
    email_matches = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*", post_text)
    if email_matches:
        application_email = email_matches[0]
        application_emails = list(dict.fromkeys(email_matches))
        application_methods.append("EMAIL")

    # Extract all URLs
    url_matches = re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w.-]*\??[\w=&]*", post_text)
    application_urls = list(dict.fromkeys(url_matches))

    for url in url_matches:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        if "google.com" in domain and "forms" in url or "forms.gle" in domain:
            application_methods.append("FORM")
            if not application_form_url: application_form_url = url
            if not application_platform: application_platform = "GOOGLE_FORMS"
            if not application_url_type: application_url_type = "FORM"
        elif "forms.office.com" in domain:
            application_methods.append("FORM")
            if not application_form_url: application_form_url = url
            if not application_platform: application_platform = "MICROSOFT_FORMS"
            if not application_url_type: application_url_type = "FORM"
        elif "typeform.com" in domain:
            application_methods.append("FORM")
            if not application_form_url: application_form_url = url
            if not application_platform: application_platform = "TYPEFORM"
            if not application_url_type: application_url_type = "FORM"
        elif "linkedin.com" in domain:
            if not application_url:
                application_url = url
                application_url_type = "LINKEDIN"
        elif "form" in url.lower():
            application_methods.append("FORM")
            if not application_form_url: application_form_url = url
            if not application_platform: application_platform = "OTHER_FORM"
        else:
            if not application_url:
                application_url = url
                application_url_type = "EXTERNAL"
    if not application_url and application_form_url:
        application_url = application_form_url


    if application_url and "FORM" not in application_methods:
        application_methods.append("EXTERNAL_LINK")


    # Direct Message Detection
    if any(re.search(pattern, text_lower) for pattern in [r"\bdm me\b", r"\bmessage me\b", r"\breach out to me\b"]):
        application_methods.append("DIRECT_MESSAGE")

    # Comment Detection
    comment_patterns = [
        r"\bcomment below\b",
        r"\bdrop a comment\b",
        r"\bdrop interested\b",
        r"\bin the comments\b",
        r"\bcomment down below\b",
        r"\bcomment interested\b"
    ]
    if any(re.search(pattern, text_lower) for pattern in comment_patterns):
        application_methods.append("COMMENT")

    application_methods = sorted(list(set(application_methods)))
    primary_method = application_methods[0] if application_methods else None

    # 4. Detect Role
    role_detected = False
    extracted_role = None
    for role_pattern in ROLE_PATTERNS:
        if re.search(role_pattern, text_lower):
            role_detected = True
            break

    # Role extraction: text around hiring keywords
    if not extracted_role:
        for keyword in ["hiring a", "looking for a", "hiring", "looking for"]:
            if keyword in text_lower:
                idx = text_lower.find(keyword) + len(keyword)
                words = post_text[idx:].strip().split()
                if len(words) >= 2:
                    extracted_role = f"{words[0]} {words[1]}".strip(".,!?;:")
                    if extracted_role.lower() not in ["for", "a", "the", "an"]:
                        role_detected = True
                        break

    if not extracted_role:
        extracted_role = None  # Use None instead of "Unknown Role" to avoid fabricating

    # 5. Numeric Confidence Scoring (0.0-1.0)
    has_email = len(application_emails) > 0
    has_url = len(application_urls) > 0
    has_application_methods = len(application_methods) > 0
    hiring_confidence_score = _calculate_confidence(hiring_intent, role_detected, has_application_methods, has_email, has_url)
    confidence_label = _confidence_level(hiring_confidence_score)

    # 6. Role Category Detection
    poster_role_category = _detect_role_category(extracted_role) if extracted_role else None

    # 7. Extract Company Name (None if not found - no fabrication)
    company_name = None
    company_patterns = [
        r"\bhiring (?:at|for)\s+([A-Z][a-zA-Z0-9&.\- ]+?)(?:\.|!|,|\n|$)",
        r"\bjoin (?:us at )?([A-Z][a-zA-Z0-9&.\- ]+?)(?:\.|!|,|\n|$)",
        r"\b(?:welcome to )?([A-Z][a-zA-Z0-9&.\- ]+?) is hiring\b"
    ]
    for pattern in company_patterns:
        match = re.search(pattern, post_text)
        if match:
            name = match.group(1).strip()
            if 2 <= len(name) <= 30 and not any(w in name.lower().split() for w in ["the", "a", "an", "our", "my", "your", "we", "us", "team"]):
                company_name = name
                break

    # 8. Detection method metadata
    detection_method = "NLP_HIRING_INTENT"

    return {
        "is_hiring_post": True,
        "confidence": confidence_label,
        "hiring_confidence_score": hiring_confidence_score,
        "job_title": extracted_role.title() if extracted_role else None,
        "company_name": company_name,
        "poster_role_category": poster_role_category,
        "hashtags": hashtags,
        "application_method": primary_method,
        "application_methods": application_methods,
        "application_email": application_email,
        "application_emails": application_emails,
        "application_url": application_url,
        "application_urls": application_urls,
        "application_platform": application_platform,
        "application_form_url": application_form_url,
        "application_url_type": application_url_type,
        "detection_method": detection_method,
        "extraction_method": "POST_TEXT_REGEX",
        "extraction_quality": "HIGH" if hiring_confidence_score >= 0.7 else ("MEDIUM" if hiring_confidence_score >= 0.4 else "LOW"),
    }

