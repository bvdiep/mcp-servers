"""
MCP IoT Server
Manages IoT devices (ThingsBoard)

Tools:
- set_attributes_light: Control light brightness
- send_chart_telemetry: Get telemetry data and generate charts
"""
import os
import asyncio
from typing import Any, Dict, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import THINGSBOARD_URL, OFFICE_TB_USERNAME, OFFICE_TB_PASSWORD
from thingsboard_adapter import ThingsBoardAPIClient
from logger import setup_server_logging


# Create MCP Server
app = Server("mcp-iot")

# Khởi tạo logger cho server này
logger = setup_server_logging("MCP-IOT")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="set_attributes_light",
            description="Control light brightness (white and yellow)",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "enum": ["tranh_a", "tranh_b", "tranh_c", "tranh_d"],
                        "description": "Device name"
                    },
                    "valueWhite": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "White light brightness (0-100)"
                    },
                    "valueYellow": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Yellow light brightness (0-100)"
                    }
                },
                "required": ["device_name"]
            }
        ),
        Tool(
            name="send_chart_telemetry",
            description="Get telemetry data and generate charts",
            inputSchema={
                "type": "object",
                "properties": {
                    "device_id": {"type": "string", "description": "ThingsBoard device ID"},
                    "telemetryKeys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Telemetry keys to fetch"
                    },
                    "startTime": {"type": "string", "description": "Start time (ISO 8601 UTC)"},
                    "endTime": {"type": "string", "description": "End time (ISO 8601 UTC)"},
                    "amount": {"type": "integer", "description": "Amount of time"},
                    "unit": {
                        "type": "string",
                        "enum": ["hour", "day", "week", "month", "year"],
                        "description": "Time unit"
                    }
                },
                "required": ["device_id", "telemetryKeys"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    logger.info(f"Received tool call: {name}")
    
    if name == "set_attributes_light":
        if not THINGSBOARD_URL or not OFFICE_TB_USERNAME:
            logger.error("ThingsBoard not configured")
            return [TextContent(type="text", text="Error: ThingsBoard not configured")]
        
        device_name = arguments.get("device_name")
        value_white = arguments.get("valueWhite", 0)
        value_yellow = arguments.get("valueYellow", 0)
        
        # Device ID mapping
        devices = {
            "tranh_a": "e9656ea0-73e1-11f0-9a58-bf99f9a3ea08",
            "tranh_b": "f5f36410-73e1-11f0-9a58-bf99f9a3ea08",
            "tranh_c": "fd9c4c40-73e1-11f0-9a58-bf99f9a3ea08",
            "tranh_d": "05f9b760-73e2-11f0-9a58-bf99f9a3ea08"
        }
        
        device_id = devices.get(device_name)
        if not device_id:
            logger.warning(f"[set_attributes_light] Unknown device: {device_name}")
            return [TextContent(type="text", text=f"Unknown device: {device_name}")]
        
        logger.info(f"[set_attributes_light] Setting {device_name}: White {value_white}%, Yellow {value_yellow}%")
        
        try:
            # Calculate PWM (0-1023)
            max_pwm = 1023
            pwm_white = int((value_white / 100) * max_pwm)
            pwm_yellow = int((value_yellow / 100) * max_pwm)
            
            data = {
                "pwmValueWhite": pwm_white,
                "pwmValueYellow": pwm_yellow
            }
            
            tb = await ThingsBoardAPIClient(THINGSBOARD_URL, OFFICE_TB_USERNAME, OFFICE_TB_PASSWORD).init()
            await tb.set_shared_attribute(device_id, data)
            await tb.close()
            
            logger.info(f"[set_attributes_light] Successfully set attributes for {device_name}")
            return [TextContent(type="text", text=f"Set {device_name}: White {value_white}%, Yellow {value_yellow}%")]
        except Exception as e:
            logger.error(f"[set_attributes_light] Error: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "send_chart_telemetry":
        if not THINGSBOARD_URL or not OFFICE_TB_USERNAME:
            logger.error("ThingsBoard not configured")
            return [TextContent(type="text", text="Error: ThingsBoard not configured")]
        
        device_id = arguments.get("device_id")
        telemetry_keys = arguments.get("telemetryKeys", [])
        start_time = arguments.get("startTime")
        end_time = arguments.get("endTime")
        amount = arguments.get("amount")
        unit = arguments.get("unit")
        
        if not device_id or not telemetry_keys:
            logger.warning("[send_chart_telemetry] Missing device_id or telemetryKeys")
            return [TextContent(type="text", text="Error: device_id and telemetryKeys required")]
        
        logger.info(f"[send_chart_telemetry] Fetching telemetry for device {device_id}, keys: {telemetry_keys}")
        
        try:
            tb = await ThingsBoardAPIClient(THINGSBOARD_URL, OFFICE_TB_USERNAME, OFFICE_TB_PASSWORD).init()
            
            # Process time parameters
            from datetime import datetime, timedelta, timezone
            
            if not end_time:
                end_time = datetime.now(timezone.utc).isoformat()
            
            if amount and unit:
                hours_map = {"hour": 1, "day": 24, "week": 24*7, "month": 24*30, "year": 365*24}
                hours = hours_map.get(unit, 1) * amount
                dt_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                dt_start = dt_end - timedelta(hours=hours)
                start_time = dt_start.isoformat()
            elif not start_time:
                start_time = end_time
            
            # Convert to milliseconds
            dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            dt_end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            start_ms = int(dt_start.timestamp() * 1000)
            end_ms = int(dt_end.timestamp() * 1000)
            
            # Get telemetry
            data = await tb.get_telemetry_from_to(device_id, telemetry_keys, start_ms, end_ms)
            data_df, short_txt, txt_for_llm = tb.process_thingsboard_telemetry(data, telemetry_keys)
            
            await tb.close()
            
            if data_df is None or data_df.empty:
                logger.warning("[send_chart_telemetry] No data in selected time range")
                return [TextContent(type="text", text="No data in selected time range")]
            
            logger.info("[send_chart_telemetry] Telemetry fetch completed")
            output = f"📊 Telemetry Data\n"
            output += f"Time range: {start_time} to {end_time}\n\n"
            output += txt_for_llm or short_txt
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            logger.error(f"[send_chart_telemetry] Error: {e}", exc_info=True)
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
