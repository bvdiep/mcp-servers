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
from mcp.server.gradient import Gradient

# Import adapters
from config import (
    EMAIL_USERNAME, EMAIL_APP_PASSWORD, EMAIL_IMAP_SERVER,
    OPENWEATHER_API_KEY
)
from email_adapter import read_emails as fetch_emails
from weather_adapter import get_weather_forecast, get_current_time


# Create MCP Server
app = Server("mcp-communication")


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
    
    if name == "read_emails":
        if not EMAIL_USERNAME or not EMAIL_APP_PASSWORD:
            return [TextContent(type="text", text="Error: Email not configured")]
        
        n_hours = arguments.get("n_hours", 12)
        
        try:
            result = await fetch_emails(
                EMAIL_IMAP_SERVER,
                EMAIL_USERNAME,
                EMAIL_APP_PASSWORD,
                n_hours
            )
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_weather_forecast":
        if not OPENWEATHER_API_KEY:
            return [TextContent(type="text", text="Error: OPENWEATHER_API_KEY not configured")]
        
        city = arguments.get("city", "Hanoi")
        days = arguments.get("days", 5)
        
        try:
            result = await get_weather_forecast(OPENWEATHER_API_KEY, city, days)
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_current_time":
        city = arguments.get("city", "Hanoi")
        
        try:
            result = get_current_time(city)
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(
                instructions="MCP Communication Server - Email and Weather",
                gradient=Gradient("#3B82F6", "#1D4ED8")
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
