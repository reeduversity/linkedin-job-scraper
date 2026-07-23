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

def parse_post(post_text: str) -> dict[str, Any]:
    """
    Parses a LinkedIn post to determine if it is a HIRING_POST and extracts relevant metadata.
    """
    if not post_text:
        return {"is_hiring_post": False}

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
        return {"is_hiring_post": False}
        
    # 2. Extract Application Methods
    application_methods = []
    application_email = None
    application_url = None
    application_platform = None
    
    # Extract Email
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*", post_text)
    if email_match:
        application_email = email_match.group(0)
        application_methods.append("EMAIL")
        
    # Extract URLs
    url_matches = re.findall(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w.-]*\??[\w=&]*", post_text)
    
    for url in url_matches:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        if "google.com" in domain and "forms" in url or "forms.gle" in domain:
            application_methods.append("FORM")
            if not application_url: application_url = url
            if not application_platform: application_platform = "GOOGLE_FORMS"
        elif "forms.office.com" in domain:
            application_methods.append("FORM")
            if not application_url: application_url = url
            if not application_platform: application_platform = "MICROSOFT_FORMS"
        elif "typeform.com" in domain:
            application_methods.append("FORM")
            if not application_url: application_url = url
            if not application_platform: application_platform = "TYPEFORM"
        elif "form" in url.lower():
            application_methods.append("FORM")
            if not application_url: application_url = url
            if not application_platform: application_platform = "OTHER_FORM"
        elif not application_url:
            application_url = url

    if application_url and "FORM" not in application_methods:
        application_methods.append("EXTERNAL_LINK")
        
    # Direct Message Detection
    if any(re.search(pattern, text_lower) for pattern in [r"\bdm me\b", r"\bmessage me\b", r"\breach out to me\b"]):
        application_methods.append("DIRECT_MESSAGE")
        
    application_methods = sorted(list(set(application_methods)))
    primary_method = application_methods[0] if application_methods else None

    # 3. Detect Role
    role_detected = False
    extracted_role = None
    for role_pattern in ROLE_PATTERNS:
        if re.search(role_pattern, text_lower):
            role_detected = True
            break
            
    # Simple role extraction fallback: text around hiring keywords
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
        extracted_role = "Unknown Role"

    # 4. Confidence Scoring
    confidence = "LOW"
    if hiring_intent and role_detected and application_methods:
        confidence = "HIGH"
    elif hiring_intent and (role_detected or application_methods):
        confidence = "MEDIUM"
        
    return {
        "is_hiring_post": True,
        "confidence": confidence,
        "job_title": extracted_role.title(),
        "application_method": primary_method,
        "application_methods": application_methods,
        "application_email": application_email,
        "application_url": application_url,
        "application_platform": application_platform
    }
