"""
Serper Adapter - Standalone version for MCP Internet Search Server
"""
import requests
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SerperAdapter:
    """Adapter for Serper API (Google Search)"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"
    
    def search(self, query: str, search_type: str = "general") -> Dict:
        """Perform a search query"""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": 10
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Serper search failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"Serper error: {e}")
            return {}
    
    def get_organic_results(self, data: Dict) -> tuple:
        """Extract organic results from search data"""
        organic = data.get("organic", [])
        
        # Extract snippets
        snippets = []
        for result in organic:
            snippet = result.get("snippet", "")
            title = result.get("title", "")
            link = result.get("link", "")
            snippets.append({
                "title": title,
                "snippet": snippet,
                "link": link
            })
        
        return snippets, organic


async def search_internet(api_key: str, query: str) -> Dict[str, Any]:
    """Search the internet using Serper"""
    if not api_key:
        return {
            "type": "text",
            "text": "Chưa cấu hình SERPER_API_KEY",
            "photos": []
        }
    
    adapter = SerperAdapter(api_key)
    data = adapter.search(query)
    
    snippets, organic_results = adapter.get_organic_results(data)
    
    if not organic_results:
        return {
            "type": "text",
            "text": f"Không tìm thấy kết quả cho: {query}",
            "photos": []
        }
    
    output = f"**Kết quả tìm kiếm cho**: {query}\n\n"
    
    for i, result in enumerate(snippets[:5], 1):
        output += f"--- Kết quả {i}: {result['title']} ---\n"
        output += f"{result['snippet']}\n"
        output += f"Nguồn: {result['link']}\n\n"
    
    return {
        "type": "text",
        "text": output,
        "photos": []
    }