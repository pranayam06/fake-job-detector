import whois
from datetime import datetime
from typing import Optional
import re

class DomainVerifier:
    def extract_domain_from_email(self, email: str) -> Optional[str]:
        if not email or "@" not in email:
            return None

        try:
            domain = email.split('@')[1].lower()
            return domain
        except:
            return None 

    def extract_domain_from_url(self, url: str) -> Optional[str]:
        if not url:
            return None
        
        url = re.sub(r'https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        domain = url.split('/')[0].lower()
        
        return domain if domain else None