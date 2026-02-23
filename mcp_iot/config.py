"""
Configuration for MCP IoT Server
Uses environment variables for configuration
"""
import os

# ThingsBoard Configuration
THINGSBOARD_URL = os.getenv("THINGSBOARD_URL", "https://thingsboard.bsmlabs.ai")
OFFICE_TB_USERNAME = os.getenv("OFFICE_TB_USERNAME", "")
OFFICE_TB_PASSWORD = os.getenv("OFFICE_TB_PASSWORD", "")

# Device ID Mappings (JSON format in env)
DEVICE_MAPPING = os.getenv("DEVICE_MAPPING", """{
    "tranh_a": "e9656ea0-73e1-11f0-9a58-bf99f9a3ea08",
    "tranh_b": "f5f36410-73e1-11f0-9a58-bf99f9a3ea08",
    "tranh_c": "fd9c4c40-73e1-11f0-9a58-bf99f9a3ea08",
    "tranh_d": "05f9b760-73e2-11f0-9a58-bf99f9a3ea08"
}""")

def get_device_id(device_name: str) -> str | None:
    """Get device ID from device name"""
    import json
    try:
        mapping = json.loads(DEVICE_MAPPING)
        return mapping.get(device_name.lower())
    except:
        return None
