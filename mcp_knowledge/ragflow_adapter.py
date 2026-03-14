"""
Ragflow Adapter - Standalone version for MCP Knowledge Server
"""
import aiohttp
import json
import logging
import os
from typing import Dict, Any, List

from config import RAGFLOW_SIMILARITY_THRESHOLD

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
        # Auto-initialize session if not already done
        if not self.session:
            await self.init()
        # Map knowledge base names to Ragflow IDs
        # Note: lily and ruatrangnguyen currently use the same dataset ID (aliases)
        knowledge_map = {
            "lily": "5370af40ed0311f0b9726abec7375c26",
            "ruatrangnguyen": "5370af40ed0311f0b9726abec7375c26",  # Same as lily for now
            "yte": "healthcare-id",
            "company": "company-id",
            "private": "private-id"
        }
        
        default_id = knowledge_map.get("lily", "5370af40ed0311f0b9726abec7375c26")
        dataset_id = knowledge_map.get(knowledge_base, default_id)
        
        url = f"{self.base_url}/api/v1/retrieval"
        top_k = 5
        
        # Get configurable similarity threshold (default 0.2 for better quality)
        similarity_threshold = RAGFLOW_SIMILARITY_THRESHOLD
        
        payload = {
            "question": query,
            "top_k": 256, # số lượng chunks đưa vào rerank
            "page": 1,
            "page_size": top_k,
            "rerank_id": "rerank-2@Voyage AI",
            "vector_similarity_weight": 0.4, # trọng số khi kết hợp semantic và keyword search
            "similarity_threshold": similarity_threshold,
            "use_kg": False,
            "dataset_ids": [dataset_id]
        }
                
        try:
            response = await self.session.post(url, json=payload)
            response.raise_for_status() # Kiểm tra lỗi 4xx, 5xx từ HTTP
            result = await response.json()
        except Exception as e:
            logger.error(f"Lỗi kết nối hoặc parse JSON: {e}")
            return {
                "text": "Lỗi kết nối hoặc parse JSON",
                "references": []
            }
        
        output_txt = ""
        if result.get("code") == 0:
            raw_chunks = result.get("data", {}).get("chunks", [])
            
            # Chuyển đổi sang cấu trúc bạn mong muốn
            for c in raw_chunks:
                output_txt += f"Nguồn: {c.get('document_keyword')}\n{c.get('content')}\n\n"
        else:
            logger.error(f"Lỗi API: {result.get('message')}")
            output_txt += "Lỗi khi truy vấn dữ liệu"
        return {
            "text": output_txt,
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
