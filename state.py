from typing import TypedDict, List, Optional, Annotated
from dataclasses import dataclass
import operator

@dataclass
class RedFlag:
    # shows a sus job posting
    category: str  # "language", "company", "requirements", "contact"
    severity: str  # "low", "medium", "high", "critical"
    finding: str   # What was found
    evidence: str  # Supporting evidence
    confidence: float  # 0.0 to 1.0

class JobAnalysisState(TypedDict):
    """State that flows through the graph"""
    # Input
    job_posting: str
    
    # Extracted information
    company_name: Optional[str]
    job_title: Optional[str]
    requirements: Optional[List[str]]
    contact_info: Optional[dict]
    salary_range: Optional[str]
    
    # Analysis results from each agent
    language_flags: Annotated[List[RedFlag], operator.add]
    company_flags: Annotated[List[RedFlag], operator.add]
    requirements_flags: Annotated[List[RedFlag], operator.add]
    
    # Final synthesis
    legitimacy_score: Optional[int]  # 0-100
    risk_level: Optional[str]  # "low", "medium", "high", "critical"
    explanation: Optional[str]
    recommendations: Optional[List[str]]