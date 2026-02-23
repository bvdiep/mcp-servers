"""
MCP Media & Analytics Server
Manages photos (Immich) and BI analytics (Metabase)

Tools:
- query_photo: Search photos by description
- get_random_photo: Get random photo
- check_attendance: Check team attendance
- get_ai_review_data: Get AI code review data
- query_telemetry_metabase: Query telemetry from Metabase
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
    IMMICH_URL, IMMICH_USERNAME, IMMICH_PASSWORD, IMMICH_ALBUM_ID,
    BI_API_KEY, BI_BASE_URL, CODE_REVIEW_DB_ID, BSMLABS_MYSQL_ID, BSMLABS_POSTGRES_ID
)
from immich_adapter import query_photo, get_random_photo
from metabase_adapter import check_attendance, get_ai_review_data, query_telemetry_metabase


# Create MCP Server
app = Server("mcp-media-analytics")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="query_photo",
            description="Search photos by description",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User request"},
                    "vision_query": {"type": "string", "description": "Visual description"},
                    "persons": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "People to include"
                    },
                    "amount": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Number of photos",
                        "default": 1
                    }
                },
                "required": ["vision_query"]
            }
        ),
        Tool(
            name="get_random_photo",
            description="Get a random photo",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="check_attendance",
            description="Check team attendance",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date (YYYY-MM-DD)"},
                    "team": {
                        "type": "string",
                        "enum": ["dev", "tech", "media", "marketing", "account", "hr"],
                        "description": "Team name"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_ai_review_data",
            description="Get AI code review statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project code"},
                    "member": {"type": "string", "description": "Member username"},
                    "start_time": {"type": "string", "description": "Start time (ISO 8601)"},
                    "end_time": {"type": "string", "description": "End time (ISO 8601)"},
                    "limit": {"type": "integer", "description": "Max results", "default": 60}
                },
                "required": []
            }
        ),
        Tool(
            name="query_telemetry_metabase",
            description="Query telemetry data from Metabase",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_id": {"type": "integer", "description": "Device ID"},
                    "telemetry_keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Telemetry keys"
                    },
                    "start_date": {"type": "string", "description": "Start date (ISO 8601)"},
                    "end_date": {"type": "string", "description": "End date (ISO 8601)"}
                },
                "required": ["device_id", "telemetry_keys"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    if name == "query_photo":
        if not IMMICH_USERNAME or not IMMICH_PASSWORD:
            return [TextContent(type="text", text="Error: Immich not configured")]
        
        query = arguments.get("query", "")
        vision_query = arguments.get("vision_query", "")
        persons = arguments.get("persons", [])
        amount = arguments.get("amount", 1)
        
        try:
            result = await query_photo(
                IMMICH_URL, IMMICH_USERNAME, IMMICH_PASSWORD,
                query, vision_query, persons, amount, IMMICH_ALBUM_ID
            )
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_random_photo":
        if not IMMICH_USERNAME or not IMMICH_PASSWORD:
            return [TextContent(type="text", text="Error: Immich not configured")]
        
        try:
            result = await get_random_photo(
                IMMICH_URL, IMMICH_USERNAME, IMMICH_PASSWORD,
                IMMICH_ALBUM_ID
            )
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "check_attendance":
        if not BI_API_KEY or not BI_BASE_URL:
            return [TextContent(type="text", text="Error: BI not configured")]
        
        date = arguments.get("date")
        team = arguments.get("team")
        
        try:
            result = await check_attendance(
                BI_API_KEY, BI_BASE_URL, BSMLABS_MYSQL_ID,
                date, team
            )
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_ai_review_data":
        if not BI_API_KEY or not BI_BASE_URL:
            return [TextContent(type="text", text="Error: BI not configured")]
        
        project = arguments.get("project")
        member = arguments.get("member")
        start_time = arguments.get("start_time")
        end_time = arguments.get("end_time")
        limit = arguments.get("limit", 60)
        
        try:
            result = await get_ai_review_data(
                BI_API_KEY, BI_BASE_URL, CODE_REVIEW_DB_ID,
                project, member, start_time, end_time, limit
            )
            return [TextContent(type="text", text=result.get("text", ""))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "query_telemetry_metabase":
        if not BI_API_KEY or not BI_BASE_URL:
            return [TextContent(type="text", text="Error: BI not configured")]
        
        device_id = arguments.get("device_id")
        telemetry_keys = arguments.get("telemetry_keys", [])
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        
        if not device_id or not telemetry_keys:
            return [TextContent(type="text", text="Error: device_id and telemetry_keys required")]
        
        try:
            result = await query_telemetry_metabase(
                BI_API_KEY, BI_BASE_URL, BSMLABS_POSTGRES_ID,
                device_id, telemetry_keys, start_date, end_date
            )
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
                instructions="MCP Media & Analytics Server - Photos and BI",
                gradient=Gradient("#EC4899", "#DB2777")
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
