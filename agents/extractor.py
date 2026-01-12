import os
from groq import Groq
from dotenv import load_dotenv
from state import JobAnalysisState
import json
import re

load_dotenv()

class ExtractorAgent:
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile" 

    # model choice: slower with 70 params (about 2-3 seconds per request)
    
    def extract(self, state: JobAnalysisState) -> dict:
        """
        Extract structured info from job posting
        
        Returns dict with updates to state:
        - company_name
        - job_title
        - requirements
        - contact_info
        - salary_range
        """
        job_posting = state['job_posting']
        
        prompt = f"""You are an expert at analyzing job postings and extracting structured information.

Given this job posting, extract the following information in JSON format:

1. company_name: The company's name (if mentioned)
2. job_title: The job title/position
3. requirements: List of key requirements (experience, skills, education)
4. contact_info: Dict with email, phone, website if mentioned
5. salary_range: Salary information if mentioned (or "Not specified")
6. location: Job location (remote/city/etc)

Job Posting:
{job_posting}

Return ONLY valid JSON with these fields. If something isn't mentioned, use null or empty list.
Example format:
{{
    "company_name": "Acme Corp",
    "job_title": "Senior Software Engineer",
    "requirements": ["5+ years Python", "Bachelor's degree", "Remote work experience"],
    "contact_info": {{
        "email": "jobs@acme.com",
        "phone": null,
        "website": "acme.com"
    }},
    "salary_range": "$120k-150k",
    "location": "Remote"
}}

Your JSON response:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You extract structured information from job postings and return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=1000
            )
            
            # Get the response text
            response_text = response.choices[0].message.content.strip()
            
            # Sometimes LLMs wrap JSON in markdown code blocks, clean that up
            response_text = self._clean_json_response(response_text)
            
            # Parse JSON
            extracted = json.loads(response_text)
            
            # Validate and clean the extracted data
            result = {
                'company_name': extracted.get('company_name'),
                'job_title': extracted.get('job_title'),
                'requirements': extracted.get('requirements', []),
                'contact_info': extracted.get('contact_info', {}),
                'salary_range': extracted.get('salary_range'),
            }
            
            # Add location to contact_info for convenience
            if 'location' in extracted:
                result['contact_info']['location'] = extracted['location']
            
            print(f"✓ Extracted: {result['company_name']} - {result['job_title']}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"✗ Failed to parse JSON from extractor: {e}")
            print(f"Response was: {response_text[:200]}")
            
            # Fallback: try to extract basic info with regex
            return self._fallback_extraction(job_posting)
            
        except Exception as e:
            print(f"✗ Extractor error: {e}")
            return {
                'company_name': None,
                'job_title': None,
                'requirements': [],
                'contact_info': {},
                'salary_range': None
            }
    
    def _clean_json_response(self, text: str) -> str:
        """Remove markdown code blocks and other formatting"""
        # Remove ```json and ``` markers
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        return text.strip()
    
    def _fallback_extraction(self, job_posting: str) -> dict:
        """Simple regex-based extraction if LLM JSON parsing fails"""
        result = {
            'company_name': None,
            'job_title': None,
            'requirements': [],
            'contact_info': {},
            'salary_range': None
        }
        
        # Try to find email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', job_posting)
        if email_match:
            result['contact_info']['email'] = email_match.group(0)
        
        # Try to find URL
        url_match = re.search(r'https?://[^\s]+|www\.[^\s]+', job_posting)
        if url_match:
            result['contact_info']['website'] = url_match.group(0)
        
        # Try to find salary
        salary_match = re.search(r'\$[\d,]+k?[-–]\$?[\d,]+k?|\$[\d,]+k?', job_posting, re.IGNORECASE)
        if salary_match:
            result['salary_range'] = salary_match.group(0)
        
        print("⚠ Used fallback extraction (regex)")
        return result

# Global instance
extractor_agent = ExtractorAgent()

# LangGraph node function
def extract_info_node(state: JobAnalysisState) -> dict:
    """LangGraph node that runs the extractor agent"""
    return extractor_agent.extract(state)