"""
MCP Communication Server
Manages email and weather

Tools:
- read_emails: Read recent emails from inbox
- get_weather_forecast: Get weather forecast
- get_current_time: Get current time
"""
import asyncio
from typing import Any, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import (
    EMAIL_USERNAME, EMAIL_APP_PASSWORD, EMAIL_IMAP_SERVER,
    OPENWEATHER_API_KEY
)
from email_adapter import read_emails as fetch_emails
from weather_adapter import get_weather_forecast, get_current_time
from logger import setup_server_logging


# Create MCP Server
app = Server("mcp-communication")

# Khởi tạo logger cho server này
logger = setup_server_logging("MCP-COMMUNICATION")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="read_emails",
            description="Read recent emails from inbox",
            inputSchema={
                "type": "object",
                "properties": {
                    "n_hours": {
                        "type": "integer",
                        "description": "Number of hours to look back",
                        "default": 12
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_weather_forecast",
            description="Get weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "enum": ["Hanoi", "Ho Chi Minh City", "Da Nang", "Can Tho", "Hai Phong"],
                        "description": "City name",
                        "default": "Hanoi"
                    },
                    "days": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Number of days",
                        "default": 5
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_current_time",
            description="Get current time for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name",
                        "default": "Hanoi"
                    }
                },
                "required": []
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    logger.info(f"Received tool call: {name}")
    
    if name == "read_emails":
        if not EMAIL_USERNAME or not EMAIL_APP_PASSWORD:
            logger.error("Email not configured")
            return [TextContent(type="text", text="Error: Email not configured")]
        
        n_hours = arguments.get("n_hours", 12)
        logger.info(f"[read_emails] Reading emails from last {n_hours} hours")
        
        try:
            result = await fetch_emails(
                EMAIL_IMAP_SERVER,
                EMAIL_USERNAME,
                EMAIL_APP_PASSWORD,
                n_hours
            )
            logger.info("[read_emails] Email fetch completed")
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            logger.error(f"[read_emails] Error: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_weather_forecast":
        if not OPENWEATHER_API_KEY:
            logger.error("OPENWEATHER_API_KEY not configured")
            return [TextContent(type="text", text="Error: OPENWEATHER_API_KEY not configured")]
        
        city = arguments.get("city", "Hanoi")
        days = arguments.get("days", 5)
        logger.info(f"[get_weather_forecast] City: {city}, Days: {days}")
        
        try:
            result = await get_weather_forecast(OPENWEATHER_API_KEY, city, days)
            logger.info("[get_weather_forecast] Weather fetch completed")
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            logger.error(f"[get_weather_forecast] Error: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_current_time":
        city = arguments.get("city", "Hanoi")
        logger.info(f"[get_current_time] City: {city}")
        
        try:
            result = get_current_time(city)
            logger.info("[get_current_time] Time fetch completed")
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            logger.error(f"[get_current_time] Error: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    logger.warning(f"Unknown tool called: {name}")
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
