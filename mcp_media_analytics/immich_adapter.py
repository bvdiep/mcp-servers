"""
Immich Adapter - Standalone version for MCP Media & Analytics Server
Photo album management using Immich API
"""
import requests
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ImmichClient:
    """Client for Immich Photo API"""
    
    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.session = None
        self.access_token = None
    
    def connect(self) -> bool:
        """Login and get access token"""
        try:
            # Login
            response = requests.post(
                f"{self.url}/api/auth/login",
                json={"email": self.username, "password": self.password}
            )
            if response.status_code != 200:
                logger.error(f"Login failed: {response.status_code}")
                return False
            
            data = response.json()
            self.access_token = data.get("accessToken")
            
            if not self.access_token:
                logger.error("No access token received")
                return False
            
            # Create session with token
            self.session = requests.Session()
            self.session.headers.update({"Authorization": f"Bearer {self.access_token}"})
            
            return True
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close the session"""
        if self.session:
            self.session = None
        self.access_token = None
    
    def smart_search(
        self,
        query: str,
        page: int = 1,
        size: int = 10,
        person_ids: Optional[List[str]] = None,
        album_ids: Optional[List[str]] = None,
        allow_video: bool = False
    ) -> List[Dict[str, Any]]:
        """Search photos using smart search"""
        if not self.session:
            return []
        
        try:
            payload = {
                "query": query,
                "page": page,
                "size": size,
                "allowVideos": allow_video
            }
            
            if person_ids:
                payload["withPeople"] = person_ids
            
            if album_ids:
                payload["albumId"] = album_ids[0]  # API expects single album
            
            response = self.session.post(
                f"{self.url}/api/search",
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Search failed: {response.status_code}")
                return []
            
            data = response.json()
            return data.get("assets", [])
        except Exception as e:
            logger.error(f"Smart search error: {e}")
            return []
    
    def get_all_named_persons(self) -> List[Dict[str, Any]]:
        """Get all named people in the album"""
        if not self.session:
            return []
        
        try:
            response = self.session.get(f"{self.url}/api/person")
            if response.status_code != 200:
                return []
            
            persons = response.json()
            # Filter only named persons
            return [p for p in persons if p.get("name")]
        except Exception as e:
            logger.error(f"Get persons error: {e}")
            return []
    
    def download_asset(self, asset_id: str, output_dir: str = "temp") -> Optional[str]:
        """Download an asset/photo"""
        if not self.session:
            return None
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            response = self.session.get(
                f"{self.url}/api/assets/{asset_id}/download",
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"Download failed: {response.status_code}")
                return None
            
            # Get filename from header or generate one
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                filename = f"photo_{asset_id}.jpg"
            
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def get_asset_metadata(self, asset_id: str) -> Dict[str, Any]:
        """Get metadata for an asset"""
        if not self.session:
            return {}
        
        try:
            response = self.session.get(f"{self.url}/api/assets/{asset_id}")
            if response.status_code != 200:
                return {}
            
            return response.json()
        except Exception as e:
            logger.error(f"Metadata error: {e}")
            return {}


# --- Tool Functions ---

async def query_photo(
    immich_url: str,
    immich_username: str,
    immich_password: str,
    query: str,
    vision_query: str,
    persons: List[str] = None,
    amount: int = 1,
    album_id: str = None
) -> Dict[str, Any]:
    """Search and retrieve photos from Immich"""
    if not immich_username or not immich_password:
        return {
            "type": "text",
            "text": "Chưa cấu hình IMMICH_USERNAME và IMMICH_PASSWORD",
            "photos": []
        }
    
    client = ImmichClient(immich_url, immich_username, immich_password)
    
    try:
        if not client.connect():
            return {
                "type": "text",
                "text": "Không thể kết nối đến Immich",
                "photos": []
            }
        
        # Prepare search parameters
        album_ids = [album_id] if album_id else None
        
        # Search
        assets = client.smart_search(
            query=vision_query,
            page=1,
            size=amount,
            person_ids=persons,
            album_ids=album_ids,
            allow_video=False
        )
        
        if not assets:
            return {
                "type": "text",
                "text": "Không tìm thấy ảnh nào phù hợp",
                "photos": []
            }
        
        # Download photos
        photo_paths = []
        for asset in assets[:amount]:
            path = client.download_asset(asset["id"], "temp")
            if path:
                photo_paths.append(path)
        
        return {
            "type": "photo",
            "text": f"Tìm thấy {len(photo_paths)} ảnh",
            "photos": photo_paths
        }
    
    finally:
        client.disconnect()


async def get_random_photo(
    immich_url: str,
    immich_username: str,
    immich_password: str,
    album_id: str = None
) -> Dict[str, Any]:
    """Get a random photo from album"""
    if not immich_username or not immich_password:
        return {
            "type": "text",
            "text": "Chưa cấu hình IMMICH_USERNAME và IMMICH_PASSWORD",
            "photos": []
        }
    
    client = ImmichClient(immich_url, immich_username, immich_password)
    
    try:
        if not client.connect():
            return {
                "type": "text",
                "text": "Không thể kết nối đến Immich",
                "photos": []
            }
        
        # Search for any photo
        assets = client.smart_search(
            query="",
            page=1,
            size=1,
            album_ids=[album_id] if album_id else None
        )
        
        if not assets:
            return {
                "type": "text",
                "text": "Không tìm thấy ảnh nào trong album",
                "photos": []
            }
        
        path = client.download_asset(assets[0]["id"], "temp")
        
        if path:
            return {
                "type": "photo",
                "text": "Ảnh ngẫu nhiên",
                "photos": [path]
            }
        
        return {
            "type": "text",
            "text": "Không thể tải ảnh",
            "photos": []
        }
    
    finally:
        client.disconnect()
