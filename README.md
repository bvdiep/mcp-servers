# MCP Servers

Collection of Model Context Protocol (MCP) servers for various integrations.

## Available Servers

| Module | Description | Tools |
|--------|-------------|-------|
| [`mcp_communication`](mcp_communication/) | Email, weather, and time | read_emails, get_weather_forecast, get_current_time |
| [`mcp_iot`](mcp_iot/) | IoT device management (ThingsBoard) | set_attributes_light, get_telemetry_data, get_all_devices |
| [`mcp_knowledge`](mcp_knowledge/) | Knowledge base (RAGFlow, Serper) | query_knowledge, search_web |
| [`mcp_media_analytics`](mcp_media_analytics/) | Photos (Immich) and BI (Metabase) | query_photo, check_attendance, get_ai_review_data |
| [`mcp_productivity`](mcp_productivity/) | Project (OpenProject) and scheduling | get_sprint_overview, add_schedule, get_schedules_this_week |

## Quick Start

### Installation

Each server has its own dependencies. Install them individually:

```bash
# For each server
cd mcp_<module>
pip install -r requirements.txt
```

### Configuration

Most servers use environment variables for configuration. Copy the example or set them in your environment:

```bash
# Email (mcp_communication)
export EMAIL_IMAP_SERVER="imap.zoho.com"
export EMAIL_USERNAME="your@email.com"
export EMAIL_APP_PASSWORD="your_app_password"
export OPENWEATHER_API_KEY="your_api_key"

# ThingsBoard (mcp_iot)
export THINGSBOARD_URL="https://your-instance.io"
export THINGSBOARD_USERNAME="your_username"
export THINGSBOARD_PASSWORD="your_password"

# RAGFlow (mcp_knowledge)
export RAGFLOW_API_KEY="your_ragflow_api_key"
export SERPER_API_KEY="your_serper_api_key"

# Immich (mcp_media_analytics)
export IMMICH_URL="https://your-immich-instance.com"
export IMMICH_USERNAME="your_username"
export IMMICH_PASSWORD="your_password"
export IMMICH_ALBUM_ID="your_album_id"

# Metabase (mcp_media_analytics)
export BI_API_KEY="your_metabase_api_key"
export BI_BASE_URL="https://your-metabase.com"

# OpenProject (mcp_productivity)
export OPENPROJECT_API_KEY="your_api_key"
export OPENPROJECT_BASE_URL="https://project.bsmlabs.ai"
```

### Running a Server

```bash
cd mcp_<module>
python server.py
```

## Architecture

Each MCP server follows a consistent structure:

```
mcp_<module>/
├── __init__.py          # Package initialization
├── config.py             # Configuration (environment variables)
├── server.py             # MCP server implementation
├── README.md             # Module documentation
├── requirements.txt      # Python dependencies
└── *_adapter.py          # External service adapters
```

## Development

### Adding a New Server

1. Create a new directory `mcp_<name>/`
2. Implement the adapter classes for external services
3. Create `server.py` following the MCP server pattern
4. Add `config.py` for environment variable configuration
5. Create `requirements.txt` with dependencies
6. Add module documentation to this README
