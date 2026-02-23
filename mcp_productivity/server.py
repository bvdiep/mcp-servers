"""
MCP Productivity Server
Manages project tracking (OpenProject) and scheduling

Tools:
- get_all_projects_overview: Get overview of all projects
- get_sprint_overview: Get details of a specific sprint
- add_schedule: Create a new meeting/event
- get_schedules_one_day: Get schedules for a specific day
- get_schedules_this_week: Get schedules for current week
- search_schedules: Search schedules by content
- update_schedule: Update an existing schedule
- delete_schedule: Delete/cancel a schedule
"""
import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import OP_API_KEY, OP_BASE_URL, DATABASE_URL
from openproject_adapter import OpenProjectStats
from schedule_adapter import ScheduleAdapter, get_schedules_by_week


# Create MCP Server
app = Server("mcp-productivity")

# Initialize adapters
schedule_manager = ScheduleAdapter(DATABASE_URL if DATABASE_URL else "schedules.db")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_all_projects_overview",
            description="Get overview of all projects in OpenProject",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_sprint_overview",
            description="Get details of a specific sprint",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "OpenProject ID"},
                    "sprint_id": {"type": "integer", "description": "Sprint/Version ID"}
                },
                "required": ["project_id", "sprint_id"]
            }
        ),
        Tool(
            name="add_schedule",
            description="Create a new meeting or event",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Title of the meeting"},
                    "start_time": {"type": "string", "description": "Start time (ISO 8601, GMT+7)"},
                    "end_time": {"type": "string", "description": "End time (ISO 8601, GMT+7)"},
                    "team": {"type": "string", "description": "Team name"},
                    "description": {"type": "string", "description": "Meeting description"},
                    "location": {"type": "string", "description": "Location"},
                    "type": {"type": "string", "enum": ["meeting", "milestone"], "description": "Type"}
                },
                "required": ["title", "start_time"]
            }
        ),
        Tool(
            name="get_schedules_one_day",
            description="Get schedules for a specific day",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_str": {"type": "string", "description": "Date (YYYY-MM-DD)"}
                },
                "required": ["date_str"]
            }
        ),
        Tool(
            name="get_schedules_this_week",
            description="Get schedules for current week",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_schedules",
            description="Search schedules by content",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "description": "Max results", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="update_schedule",
            description="Update an existing schedule",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "integer", "description": "Schedule ID"},
                    "new_title": {"type": "string", "description": "New title"},
                    "new_start_time": {"type": "string", "description": "New start time"},
                    "new_end_time": {"type": "string", "description": "New end time"},
                    "new_description": {"type": "string", "description": "New description"},
                    "new_location": {"type": "string", "description": "New location"}
                },
                "required": ["schedule_id"]
            }
        ),
        Tool(
            name="delete_schedule",
            description="Delete/cancel a schedule",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "integer", "description": "Schedule ID"}
                },
                "required": ["schedule_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    # OpenProject Tools
    if name == "get_all_projects_overview":
        if not OP_API_KEY or not OP_BASE_URL:
            return [TextContent(type="text", text="Error: OP_API_KEY and OP_BASE_URL not configured")]
        
        # This would normally use project mapping from config
        # For now, return placeholder
        return [TextContent(type="text", text="Error: Project mapping not configured. Set PROJECT_MAPPING_JSON")]
    
    elif name == "get_sprint_overview":
        if not OP_API_KEY or not OP_BASE_URL:
            return [TextContent(type="text", text="Error: OP_API_KEY and OP_BASE_URL not configured")]
        
        project_id = arguments.get("project_id")
        sprint_id = arguments.get("sprint_id")
        
        if not project_id or not sprint_id:
            return [TextContent(type="text", text="Error: project_id and sprint_id required")]
        
        try:
            openproject = OpenProjectStats(OP_API_KEY, OP_BASE_URL, project_id)
            status_counts, summarize, _, _ = openproject.fetch_ticket_status_counts_by_version(sprint_id)
            
            output = "## Status Counts\n"
            for status, count in status_counts.items():
                output += f"- {status}: {count}\n"
            
            output += "\n## By Assignee\n"
            for assignee, row in summarize.items():
                output += f"\n### {assignee}\n"
                for key, value in row.items():
                    output += f"- {key}: {value}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    # Schedule Tools
    elif name == "add_schedule":
        try:
            schedule_id, msg = schedule_manager.add_schedule({
                'title': arguments.get("title"),
                'start_time': arguments.get("start_time"),
                'end_time': arguments.get("end_time"),
                'team': arguments.get("team", "Dev"),
                'description': arguments.get("description"),
                'location': arguments.get("location"),
                'type': arguments.get("type", "meeting")
            })
            if schedule_id:
                return [TextContent(type="text", text=f"Created schedule with ID: {schedule_id}")]
            return [TextContent(type="text", text=f"Error: {msg}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_schedules_one_day":
        try:
            date_str = arguments.get("date_str")
            schedules = schedule_manager.get_schedules_by_date(date_str)
            
            if not schedules:
                return [TextContent(type="text", text=f"No schedules on {date_str}")]
            
            output = f"📅 Schedules for {date_str}\n\n"
            for s in schedules:
                output += f"- {s['start_time']} - {s['title']}\n"
                if s.get('location'):
                    output += f"  Location: {s['location']}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "get_schedules_this_week":
        try:
            today = datetime.now()
            from datetime import timedelta
            weekday = today.weekday()
            start_of_week = today - timedelta(days=weekday)
            end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
            
            schedules = schedule_manager.get_schedules_by_time_range(
                None,
                start_of_week.isoformat(),
                end_of_week.isoformat()
            )
            
            if not schedules:
                return [TextContent(type="text", text="No schedules this week")]
            
            output = f"📅 This Week ({len(schedules)} schedules)\n\n"
            for s in schedules:
                output += f"- {s['start_time']} - {s['title']}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "search_schedules":
        try:
            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)
            
            results = schedule_manager.search_schedules(query, top_k)
            
            if not results:
                return [TextContent(type="text", text="No schedules found")]
            
            output = f"🔍 Found {len(results)} schedules\n\n"
            for s in results:
                output += f"- {s['start_time']} - {s['title']}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "update_schedule":
        try:
            schedule_id = arguments.get("schedule_id")
            updates = {}
            
            if arguments.get("new_title"):
                updates["title"] = arguments["new_title"]
            if arguments.get("new_start_time"):
                updates["start_time"] = arguments["new_start_time"]
            if arguments.get("new_end_time"):
                updates["end_time"] = arguments["new_end_time"]
            if arguments.get("new_description"):
                updates["description"] = arguments["new_description"]
            if arguments.get("new_location"):
                updates["location"] = arguments["new_location"]
            
            schedule_manager.update_schedule(schedule_id, updates)
            return [TextContent(type="text", text=f"Updated schedule {schedule_id}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "delete_schedule":
        try:
            schedule_id = arguments.get("schedule_id")
            schedule_manager.delete_schedule(schedule_id)
            return [TextContent(type="text", text=f"Deleted schedule {schedule_id}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
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
