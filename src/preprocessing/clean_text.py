"""
Clean Text:
    - strip html tags to plain text
    - remove boilerplate (unsubscribe, privacy, phone sigs)
    - normalize spaces and lowercase
"""

import re
from bs4 import BeautifulSoup

# common footer/boilerplate bits
_BOILER = re.compile(
    r"(unsubscribe|view in browser|privacy policy|manage preferences|"
    r"update preferences|terms of service|do not reply|no[- ]reply|"
    r"confidentiality notice|to stop receiving|footer address|mailing address|"
    r"sent from my (iphone|ipad|android)|get the app|view online)",
    flags=re.IGNORECASE,
)

# simple url + email tokens (we don’t care about exact values)
_URL_OR_EMAIL = re.compile(r"(https?://\S+|www\.\S+|[\w\.-]+@[\w\.-]+)", re.IGNORECASE)

# quoted reply markers are noisy for training
_QUOTED_MARK = re.compile(r"^(>+)|^(on .+ wrote:)$", re.IGNORECASE)

def _strip_html(text: str) -> str:
    # parse html to text
    return BeautifulSoup(text, "html.parser").get_text(separator=" ")

def _drop_quoted_lines(text: str) -> str:
    # remove typical quoted reply lines
    lines = []
    for line in text.splitlines():
        if _QUOTED_MARK.search(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines)

def clean_text(text: str) -> str:
    # main cleaner
    if not text:
        return ""
    t = _strip_html(text)
    t = _drop_quoted_lines(t)
    t = _BOILER.sub(" ", t)
    t = _URL_OR_EMAIL.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip().lower()
    return t
