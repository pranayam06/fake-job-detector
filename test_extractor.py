from agents.extractor import extractor_agent

sample_posting = """
Software Engineer - Acme Corp

We're looking for a Senior Software Engineer to join our team!

Requirements:
- 5+ years Python experience
- Bachelor's in CS
- Experience with AWS

Salary: $120k-$150k
Location: Remote

Apply: jobs@acme.com
Website: www.acme.com
"""

result = extractor_agent.extract({'job_posting': sample_posting})
print(result)