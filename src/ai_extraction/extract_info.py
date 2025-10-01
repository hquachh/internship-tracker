"""
AI-Enhanced Information Extraction:
    - Use LLM to extract company, position, and candidate portal URL
    - Fallback to regex patterns if AI fails
    - Structured output for consistent data quality
"""

import re
import json
import os
from typing import Dict, Optional
import google.generativeai as genai

def extract_with_ai(subject: str, body: str, sender: str) -> Dict[str, str]:
    """
    Use AI to extract structured information from job application emails.

    Returns:
        {
            'company': str,
            'position': str,
            'candidate_portal_url': str,
            'extraction_method': 'ai' | 'regex' | 'hybrid'
        }
    """

    # Prepare the prompt for AI extraction
    email_text = f"""
    Subject: {subject}
    From: {sender}
    Body: {body[:2000]}  # Limit body length for token efficiency
    """

    extraction_prompt = f"""
    You are an expert information extraction specialist. Your job is to extract ALL possible information from this job application email. DO NOT leave fields blank unless absolutely impossible to determine.

    EMAIL TO ANALYZE:
    {email_text}

    EXTRACTION REQUIREMENTS:
    1. COMPANY: Look everywhere - subject line, sender email domain, email signature, body text. If you see "careers@microsoft.com", that's Microsoft. If subject says "Thanks for applying to Google", that's Google.

    2. POSITION: Check subject line first (often contains job title), then body. Look for words like "intern", "engineer", "analyst", "developer". Even partial matches like "Software Eng" are better than blank.

    3. LOCATION: Look for city/state mentions, addresses, office locations, "remote work", even company headquarters. If it mentions "San Francisco office" or "NYC team", extract that.

    4. PORTAL URL: Find ANY career-related URLs, application tracking links, candidate portals, or links to check application status.

    CRITICAL RULES:
    - Try MULTIPLE extraction strategies for each field
    - Use context clues and make reasonable inferences
    - Extract partial information rather than leaving blank
    - For company: email domains are often the best source
    - For position: subject lines usually contain the role
    - For location: look for any geographic mentions

    Return ONLY valid JSON (no extra text):
    {{
        "company": "extracted company name",
        "position": "extracted position title",
        "location": "extracted location or empty string if truly none found",
        "candidate_portal_url": "extracted URL or empty string if none found"
    }}
    """

    try:
        # Call AI model for extraction
        ai_result = call_ai_model(extraction_prompt)

        if ai_result and ai_result.strip():
            # Try to clean up the response and extract JSON
            clean_response = ai_result.strip()

            # Look for JSON content between ```json and ``` or just find the JSON object
            if "```json" in clean_response:
                start = clean_response.find("```json") + 7
                end = clean_response.find("```", start)
                if end != -1:
                    clean_response = clean_response[start:end].strip()
            elif clean_response.startswith("```") and clean_response.endswith("```"):
                clean_response = clean_response[3:-3].strip()

            # Find JSON object boundaries
            if "{" in clean_response and "}" in clean_response:
                start = clean_response.find("{")
                end = clean_response.rfind("}") + 1
                clean_response = clean_response[start:end]

            result = json.loads(clean_response)
            result['extraction_method'] = 'ai'
            return result
        else:
            print(f"[DEBUG] Empty or no response from Gemini API")
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON parsing failed: {e}")
        print(f"[DEBUG] Raw AI response: '{ai_result[:200]}...'")
    except Exception as e:
        print(f"[DEBUG] AI extraction failed: {e}")

    # Fallback to enhanced regex extraction
    print("[DEBUG] Falling back to regex extraction")
    return extract_with_regex(subject, body, sender)

def call_ai_model(prompt: str) -> Optional[str]:
    """
    Call Google Gemini API for AI-powered information extraction.
    """
    try:
        # Load .env file if it exists
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.strip() and '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("[DEBUG] GEMINI_API_KEY environment variable not set, using regex fallback")
            return None

        genai.configure(api_key=api_key)

        # Use Gemini 1.5 Flash model (free tier)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Generate response
        response = model.generate_content(prompt)

        if response and response.text:
            return response.text.strip()
        else:
            print("[DEBUG] Empty response from Gemini API")
            return None

    except Exception as e:
        print(f"[DEBUG] Gemini API call failed: {e}")
        return None

def extract_with_regex(subject: str, body: str, sender: str) -> Dict[str, str]:
    """
    Enhanced regex extraction with better patterns and URL detection.
    """
    full_text = f"{subject} {body}".lower()

    # Enhanced company extraction
    company = extract_company_name(subject, body, sender)

    # Enhanced position extraction
    position = extract_position_title(subject, body)

    # Extract candidate portal URL
    candidate_portal_url = extract_candidate_portal_url(body)

    return {
        'company': company,
        'position': position,
        'candidate_portal_url': candidate_portal_url,
        'extraction_method': 'regex'
    }

def extract_company_name(subject: str, body: str, sender: str) -> str:
    """Extract company name using enhanced regex patterns."""
    full_text = f"{subject} {body}".lower()

    # Try sender domain first
    if "@" in sender:
        domain = sender.split("@")[-1].lower()
        if not domain.endswith((".com", ".org", ".net", ".edu", ".gov")):
            domain = ""

        # Common company patterns from domain
        if domain and "noreply" not in domain and "careers" not in domain:
            company_from_domain = domain.split(".")[0].title()
            if len(company_from_domain) > 2:
                return company_from_domain

    # Enhanced company extraction patterns
    company_patterns = [
        r"(?:thank you for applying to|your application (?:to|at))\s+([a-z][a-z\s&.-]+?)(?:\s+for|\.|$)",
        r"(?:at|from|with)\s+([a-z][a-z\s&.-]+?)(?:\s+for|\s+–|\s+-|\s+\||\.|\s+application|$)",
        r"([a-z][a-z\s&.-]{2,25})\s+(?:application|internship|position|careers|team)",
        r"application confirmation\s+[–-]\s+([a-z][a-z\s&.-]+)",
        r"welcome to\s+([a-z][a-z\s&.-]+?)(?:\s|$)",
        r"([a-z][a-z\s&.-]{3,30})\s+talent\s+team",
        r"this is to confirm your application to\s+([a-z][a-z\s&.-]+)"
    ]

    for pattern in company_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for match in matches:
            candidate = match.strip()
            # Clean up and validate
            candidate = re.sub(r"[.,-]+$", "", candidate)
            candidate = candidate.title()
            # Exclude common false positives
            if (len(candidate) > 3 and
                candidate.lower() not in ["the", "and", "for", "with", "this", "your", "our", "team", "application"]):
                return candidate

    return ""

def extract_position_title(subject: str, body: str) -> str:
    """Extract position title using enhanced regex patterns."""
    full_text = f"{subject} {body}".lower()

    position_patterns = [
        r"(?:for the|for our|for a)\s+([a-z][a-z\s-]{5,40}?)(?:\s+position|\s+role|\s+internship|\.|$)",
        r"([a-z][a-z\s-]+?)\s+(?:internship|intern)\s+(?:position|role|application)",
        r"(?:position:|role:|applied for:)\s+([a-z][a-z\s-]+?)(?:\.|$|internship)",
        r"application for\s+([a-z][a-z\s-]+?)(?:\s+at|\s+with|\.|$)",
        r"([a-z\s-]+?)\s+(?:summer|fall|spring|winter)\s+(?:intern|internship)",
        r"(?:software|data|marketing|finance|engineering|product|design)\s+([a-z][a-z\s-]*?)\s+intern",
        r"intern[:\s-]+([a-z][a-z\s-]+?)(?:\.|$|at)"
    ]

    for pattern in position_patterns:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        for match in matches:
            candidate = match.strip()
            candidate = re.sub(r"[.,-]+$", "", candidate)
            candidate = candidate.title()
            if len(candidate) > 3 and candidate.lower() not in ["the", "and", "for", "with", "this", "your", "our"]:
                return candidate

    return ""

def extract_candidate_portal_url(body: str) -> str:
    """Extract candidate portal/application tracking URLs."""

    # URL patterns that typically lead to candidate portals
    url_patterns = [
        r"https?://[^\s]+(?:candidate|portal|application|status|track|hiring|careers|recruit)[^\s]*",
        r"https?://[^\s]*(?:workday|greenhouse|lever|bamboohr|smartrecruiters)[^\s]*",
        r"https?://[^\s]*(?:apply|jobs|careers)[^\s]*portal[^\s]*",
        r"https?://[^\s]*status[^\s]*application[^\s]*"
    ]

    for pattern in url_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            # Clean up the URL (remove trailing punctuation)
            url = re.sub(r'[.,;:!?)]+$', '', match)
            if len(url) > 10:  # Basic validation
                return url

    # Fallback: look for any HTTPS URL in application-related context
    general_urls = re.findall(r'https?://[^\s]+', body)
    for url in general_urls:
        url = re.sub(r'[.,;:!?)]+$', '', url)
        # Check if URL contains keywords that suggest it's an application portal
        if any(keyword in url.lower() for keyword in
               ['candidate', 'portal', 'status', 'application', 'track', 'hiring', 'apply']):
            return url

    return ""

# Backward compatibility function to replace existing extract_company_position
def extract_company_position_enhanced(subject: str, body: str, sender: str = "") -> tuple:
    """
    Enhanced version of the existing extract_company_position function.
    Returns (company, position) tuple for compatibility.
    """
    result = extract_with_ai(subject, body, sender)
    return result['company'], result['position']