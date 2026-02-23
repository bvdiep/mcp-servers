"""
Ragflow Adapter - Standalone version for MCP Knowledge Server
"""
import aiohttp
import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RagflowAdapter:
    """Adapter for Ragflow API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.ragflow.io/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
    
    async def init(self):
        """Initialize session"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
    
    async def query(self, query: str, knowledge_base: str = "lily") -> Dict[str, Any]:
        """Query the knowledge base"""
        # Map knowledge base names to Ragflow IDs
        knowledge_map = {
            "lily": "lily-id",
            "ruatrangnguyen": "ruatrangnguyen-id",
            "yte": "healthcare-id",
            "company": "company-id",
            "private": "private-id"
        }
        
        dataset_id = knowledge_map.get(knowledge_base, "lily-id")
        
        # Chat completion endpoint
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": "ragflow",
            "messages": [
                {"role": "user", "content": query}
            ],
            "dataset_id": dataset_id,
            "stream": False
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "text": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                        "references": data.get("references", [])
                    }
                else:
                    error = await response.text()
                    logger.error(f"Ragflow query failed: {error}")
                    return {
                        "text": f"Lỗi: {response.status}",
                        "references": []
                    }
        except Exception as e:
            logger.error(f"Ragflow error: {e}")
            return {
                "text": f"Lỗi: {str(e)}",
                "references": []
            }


async def query_knowledge(
    api_key: str,
    base_url: str,
    query: str,
    knowledge: str = "lily"
) -> Dict[str, Any]:
    """Query knowledge base"""
    if not api_key:
        return {
            "type": "text",
            "text": "Chưa cấu hình RAGFLOW_API_KEY",
            "photos": []
        }
    
    adapter = RagflowAdapter(api_key, base_url)
    await adapter.init()
    
    try:
        result = await adapter.query(query, knowledge)
        await adapter.close()
        
        text = result.get("text", "")
        references = result.get("references", [])
        
        output = text
        if references:
            output += "\n\n**Tham khảo:**\n"
            for ref in references:
                output += f"- {ref.get('document_name', 'N/A')}\n"
        
        return {
            "type": "text",
            "text": output,
            "photos": []
        }
    except Exception as e:
        await adapter.close()
        return {
            "type": "text",
            "text": f"Lỗi: {str(e)}",
            "photos": []
        }
