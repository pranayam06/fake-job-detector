import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

class WebSearchTool:

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment")
        self.client = TavilyClient(api_key=api_key)
    
    def search(self, query: str, max_results: int = 5) -> dict:
        try: 
            response = self.client.search(
                query= query, 
                search_depth = "basic", 
                max_results= max_results)
            results = []
            
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0.0)
                })
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'answer': response.get('answer', '') # llm generated response
            }
            
        except Exception as e:
            return {
                'success': False,
                'query': query,
                'error': str(e),
                'results': []
            }

    def search_company(self, company_name: str) -> dict:
        queries = [
            f"{company_name} official website",
            f"{company_name} scam reports complaints",
            f"{company_name} scam post reddit",
            f"{company_name} LinkedIn company page"
        ]
        
        all_results = {}
        for query in queries:
            all_results[query] = self.search(query, max_results=3)
        
        return all_results 

web_search = WebSearchTool()