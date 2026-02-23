"""
Weather Adapter - Standalone version for MCP Communication Server
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OpenWeatherAdapter:
    """Adapter for OpenWeather API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    async def get_forecast(self, city: str, days: int = 5) -> str:
        """Get weather forecast for a city"""
        # Map city names
        city_map = {
            "hanoi": "Hanoi",
            "ho chi minh city": "Ho Chi Minh City",
            "ho chi minh": "Ho Chi Minh City",
            "saigon": "Ho Chi Minh City",
            "da nang": "Da Nang",
            "danang": "Da Nang",
            "can tho": "Can Tho",
            "cantho": "Can Tho",
            "hai phong": "Hai Phong",
            "haiphong": "Hai Phong"
        }
        
        city_normalized = city_map.get(city.lower(), city)
        
        # Get current weather
        current_url = f"{self.base_url}/weather"
        params = {
            "q": city_normalized,
            "appid": self.api_key,
            "units": "metric"
        }
        
        try:
            async with requests.Session() as session:
                # Current weather
                response = await session.get(current_url, params=params)
                if response.status_code != 200:
                    return f"Không tìm thấy thành phố {city}"
                
                current_data = response.json()
                
                # Forecast
                forecast_url = f"{self.base_url}/forecast"
                forecast_response = await session.get(forecast_url, params=params)
                
                output = f"**Thời tiết tại {city_normalized}**\n\n"
                
                # Current weather
                temp = current_data.get("main", {}).get("temp", 0)
                humidity = current_data.get("main", {}).get("humidity", 0)
                description = current_data.get("weather", [{}])[0].get("description", "")
                
                output += f"**Hiện tại:**\n"
                output += f"- Nhiệt độ: {temp:.1f}°C\n"
                output += f"- Độ ẩm: {humidity}%\n"
                output += f"- Thời tiết: {description}\n\n"
                
                # Forecast
                if forecast_response.status_code == 200:
                    forecast_data = forecast_response.json()
                    forecasts = forecast_data.get("list", [])
                    
                    output += f"**Dự báo {days} ngày tới:**\n"
                    
                    current_day = None
                    count = 0
                    for item in forecasts:
                        dt = datetime.fromtimestamp(item["dt"])
                        day = dt.strftime("%Y-%m-%d")
                        
                        if day != current_day and count < days:
                            current_day = day
                            temp_min = item["main"].get("temp_min", 0)
                            temp_max = item["main"].get("temp_max", 0)
                            desc = item["weather"][0].get("description", "")
                            
                            output += f"\n📅 {dt.strftime('%d/%m/%Y')} ({dt.strftime('%A')}):\n"
                            output += f"   - Nhiệt độ: {temp_min:.1f}°C - {temp_max:.1f}°C\n"
                            output += f"   - Thời tiết: {desc}\n"
                            count += 1
                
                return output
                
        except Exception as e:
            logger.error(f"Weather error: {e}")
            return f"Lỗi khi lấy dữ liệu thời tiết: {str(e)}"


async def get_weather_forecast(
    api_key: str,
    city: str = "Hanoi",
    days: int = 5
) -> Dict[str, Any]:
    """Get weather forecast"""
    if not api_key:
        return {
            "type": "text",
            "text": "Chưa cấu hình OPENWEATHER_API_KEY",
            "photos": []
        }
    
    # Validate city
    valid_cities = ["hanoi", "ho chi minh city", "da nang", "can tho", "hai phong"]
    if city.lower() not in valid_cities:
        return {
            "type": "text",
            "text": "Dự báo thời tiết chỉ áp dụng cho: Hanoi, Ho Chi Minh City, Da Nang, Can Tho, Hai Phong",
            "photos": []
        }
    
    adapter = OpenWeatherAdapter(api_key)
    forecast = await adapter.get_forecast(city, days)
    
    return {
        "type": "text",
        "text": forecast,
        "photos": []
    }


def get_current_time(city: str = "Hanoi") -> Dict[str, Any]:
    """Get current time for a city"""
    import datetime
    
    if city.lower() in ["hanoi", "hà nội"]:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
        return {
            "type": "text",
            "text": f"Thời gian hiện tại ở Hà Nội là {now.strftime('%H:%M:%S ngày %d-%m-%Y')}.",
            "photos": []
        }
    
    return {
        "type": "text",
        "text": f"Em chưa biết thời gian ở {city} rồi.",
        "photos": []
    }
