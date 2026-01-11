from datetime import datetime
from typing import Optional
import re
import requests

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

    def check_domain_exists(self, domain: str) -> dict:
        flags = []

        try:
            ip_address = socket.gethostbyname(domain)
            
            return {
                'success': True,
                'exists': True,
                'domain': domain,
                'ip_address': ip_address,
                'flags': []
            }

        except socket.gaierror:
            flags.append({
                'type': 'domain_not_found',
                'severity': 'critical',
                'detail': f'Domain {domain} does not exist or cannot be resolved'
            })
            
            return {
                'success': False,
                'exists': False,
                'domain': domain,
                'ip_address': None,
                'flags': flags
            }

        except Exception as e:
            return {
                'success': False,
                'exists': False,
                'domain': domain,
                'error': str(e),
                'flags': [{
                    'type': 'verification_error',
                    'severity': 'medium',
                    'detail': f'Could not verify domain: {str(e)}'
                }]
            }
    def check_domain_age_via_api(self, domain: str) -> dict:
        """
        Check domain age using a free API
        Uses the Wayback Machine API to estimate when domain first appeared
        """
        try:
            url = f"http://archive.org/wayback/available?url={domain}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get('archived_snapshots') and data['archived_snapshots'].get('closest'):
                timestamp = data['archived_snapshots']['closest']['timestamp']
                year = int(timestamp[:4])
                month = int(timestamp[4:6])
                day = int(timestamp[6:8])
                
                first_seen = datetime(year, month, day)
                age_days = (datetime.now() - first_seen).days
                
                flags = []
                
                # Flag if domain is very new
                if age_days < 180:  # Less than 6 months
                    flags.append({
                        'type': 'new_domain',
                        'severity': 'high',
                        'detail': f'Domain first appeared only {age_days} days ago'
                    })
                elif age_days < 365:  # Less than 1 year
                    flags.append({
                        'type': 'relatively_new',
                        'severity': 'medium',
                        'detail': f'Domain is less than a year old ({age_days} days)'
                    })
                
                return {
                    'success': True,
                    'first_seen': str(first_seen),
                    'age_days': age_days,
                    'age_years': round(age_days / 365, 1),
                    'flags': flags
                }
            else:
                # No archive found - either very new or never archived
                return {
                    'success': False,
                    'error': 'No historical data found',
                    'flags': [{
                        'type': 'no_history',
                        'severity': 'high',
                        'detail': 'Domain has no web archive history - likely very new or never had content'
                    }]
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'flags': []
            }
    
    def full_domain_check(self, domain: str) -> dict:

        # First check if domain exists
        existence_check = self.check_domain_exists(domain)
        
        if not existence_check['exists']:
            return existence_check
        
        # Then check age
        age_check = self.check_domain_age_via_api(domain)
        
        # Combine results
        all_flags = existence_check.get('flags', []) + age_check.get('flags', [])
        
        return {
            'success': True,
            'exists': True,
            'domain': domain,
            'ip_address': existence_check.get('ip_address'),
            'age_info': {
                'first_seen': age_check.get('first_seen'),
                'age_days': age_check.get('age_days'),
                'age_years': age_check.get('age_years')
            },
            'flags': all_flags
        }

    def verify_email_domain(self, email: str) -> dict:

        domain = self.extract_domain_from_email(email)
        
        if not domain:
            return {
                'success': False,
                'error': 'Invalid email format',
                'flags': [{
                    'type': 'invalid_email',
                    'severity': 'medium',
                    'detail': 'Email format is invalid'
                }]
            }
        
        # Check for free email providers (MAJOR red flag for companies)
        free_providers = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'aol.com', 'protonmail.com', 'mail.com', 'icloud.com',
            'yandex.com', 'zoho.com', 'gmx.com'
        ]
        if domain in free_providers:
            return {
                'success': True,
                'domain': domain,
                'exists': True,
                'is_free_provider': True,
                'flags': [{
                    'type': 'free_email_provider',
                    'severity': 'critical',
                    'detail': f'Using free email provider ({domain}) - legitimate companies use company domains'
                }]
            }
        
        # Otherwise check if domain exists
        result = self.check_domain_exists(domain)
        result['is_free_provider'] = False
        return result

    def verify_website_domain(self, url: str) -> dict:

        domain = self.extract_domain_from_url(url)
        
        if not domain:
            return {
                'success': False,
                'error': 'Invalid URL format',
                'flags': [{
                    'type': 'invalid_url',
                    'severity': 'medium',
                    'detail': 'URL format is invalid'
                }]
            }
        
        return self.check_domain_exists(domain)

# Global instance
domain_verifier = DomainVerifier()