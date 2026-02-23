"""
ThingsBoard Adapter - Standalone version for MCP IoT Server
"""
import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ThingsBoardAPIClient:
    """Async client for ThingsBoard API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
        self.session = None
    
    async def init(self) -> "ThingsBoardAPIClient":
        """Initialize connection and authenticate"""
        self.session = aiohttp.ClientSession()
        await self.authenticate()
        return self
    
    async def authenticate(self):
        """Authenticate with ThingsBoard"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": self.username, "password": self.password}
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                self.token = data.get("token")
            else:
                raise Exception(f"Authentication failed: {response.status}")
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
    
    async def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request with auth"""
        url = f"{self.base_url}{endpoint}"
        headers = {"X-Authorization": f"Bearer {self.token}"}
        
        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"GET {endpoint} failed: {response.status}")
                return {}
    
    async def post(self, endpoint: str, data: Dict) -> Dict:
        """Make POST request with auth"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "X-Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        async with self.session.post(url, headers=headers, json=data) as response:
            if response.status in [200, 201]:
                return await response.json()
            else:
                logger.error(f"POST {endpoint} failed: {response.status}")
                return {}
    
    async def set_shared_attribute(self, device_id: str, attributes: Dict) -> bool:
        """Set shared attributes for a device"""
        endpoint = f"/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED"
        result = await self.post(endpoint, attributes)
        return bool(result)
    
    async def get_telemetry(self, device_id: str, keys: List[str], 
                           start_time: int, end_time: int) -> List[Dict]:
        """Get telemetry data for a device"""
        endpoint = f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        params = {
            "keys": ",".join(keys),
            "startTime": start_time,
            "endTime": end_time
        }
        data = await self.get(endpoint, params)
        
        results = []
        for key in keys:
            if key in data:
                for item in data[key]:
                    results.append({
                        "key": key,
                        "ts": item.get("ts"),
                        "value": item.get("value")
                    })
        
        return results


async def set_attributes_light(
    thingsboard_url: str,
    username: str,
    password: str,
    device_name: str,
    value_white: int,
    value_yellow: int
) -> Dict[str, Any]:
    """Control light brightness for a device"""
    # Device name to ID mapping
    devices = {
        "tranh_a": "e9656ea0-73e1-11f0-9a58-bf99f9a3ea08",
        "tranh_b": "f5f36410-73e1-11f0-9a58-bf99f9a3ea08",
        "tranh_c": "fd9c4c40-73e1-11f0-9a58-bf99f9a3ea08",
        "tranh_d": "05f9b760-73e2-11f0-9a58-bf99f9a3ea08"
    }
    
    device_id = devices.get(device_name.lower())
    if not device_id:
        return {
            "type": "text",
            "text": f"Không tìm thấy thiết bị '{device_name}' trong danh sách.",
            "photos": []
        }
    
    # Calculate PWM values (0-1023)
    max_pwm = 1023
    pwm_white = int((value_white / 100) * max_pwm)
    pwm_yellow = int((value_yellow / 100) * max_pwm)
    
    data = {
        "pwmValueWhite": pwm_white,
        "pwmValueYellow": pwm_yellow
    }
    
    try:
        client = await ThingsBoardAPIClient(thingsboard_url, username, password).init()
        await client.set_shared_attribute(device_id, data)
        await client.close()
        
        return {
            "type": "text",
            "text": f"Đã thực hiện đặt đèn '{device_name}' ở chế độ: Trắng {value_white}% và Vàng {value_yellow}%.",
            "photos": []
        }
    except Exception as e:
        logger.error(f"Error setting ThingsBoard attributes: {e}")
        return {
            "type": "text",
            "text": f"Lỗi: {str(e)}",
            "photos": []
        }


async def get_telemetry_data(
    thingsboard_url: str,
    username: str,
    password: str,
    device_id: str,
    telemetry_keys: List[str],
    start_time: str | None = None,
    end_time: str | None = None,
    amount: int | None = None,
    unit: str | None = None
) -> Dict[str, Any]:
    """Get telemetry data from a device"""
    # Parse time
    if not end_time:
        end_time = datetime.now(timezone.utc).isoformat()
    
    dt_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    end_ms = int(dt_end.timestamp() * 1000)
    
    if not start_time and amount and unit:
        # Calculate start time from amount/unit
        hours_map = {"hour": 1, "day": 24, "week": 168, "month": 720, "year": 8760}
        hours = hours_map.get(unit, 1) * amount
        dt_start = dt_end - timedelta(hours=hours)
        start_ms = int(dt_start.timestamp() * 1000)
    elif start_time:
        dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        start_ms = int(dt_start.timestamp() * 1000)
    else:
        start_ms = end_ms
    
    try:
        client = await ThingsBoardAPIClient(thingsboard_url, username, password).init()
        data = await client.get_telemetry(device_id, telemetry_keys, start_ms, end_ms)
        await client.close()
        
        # Process data
        if not data:
            return {
                "type": "text",
                "text": f"Không có dữ liệu trong khoảng thời gian",
                "photos": []
            }
        
        # Simple summary
        summary = f"Lấy được {len(data)} điểm dữ liệu"
        
        return {
            "type": "text",
            "text": summary,
            "data": data
        }
    except Exception as e:
        logger.error(f"Error getting telemetry: {e}")
        return {
            "type": "text",
            "text": f"Lỗi: {str(e)}",
            "photos": []
        }
