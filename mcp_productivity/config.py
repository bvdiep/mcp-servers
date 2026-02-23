"""
Configuration for MCP Productivity Server
Uses environment variables for configuration
"""
import os
from typing import Dict, Any, List, Optional

# OpenProject Configuration
OP_API_KEY = os.getenv("OPENPROJECT_API_KEY", "")
OP_BASE_URL = os.getenv("OPENPROJECT_BASE_URL", "https://project.bsmlabs.ai")

# Database Configuration (SQLite for local storage)
DATABASE_URL = os.getenv("DATABASE_URL", "schedules.db")

# Schedule Configuration
THRESHOLD_SIMILARITY_DISTANCE_EASY = float(os.getenv("THRESHOLD_SIMILARITY_DISTANCE_EASY", "0.35"))

# Project-Sprint Mapping (can be loaded from env or file)
PROJECT_SPRINT_MAPPING = {
    "projects": [
        {"id": 13, "name": "TrucTam"}
    ],
    "assignees": []
}

def load_project_mapping() -> Dict[str, Any]:
    """Load project mapping from environment or use default"""
    mapping_json = os.getenv("PROJECT_SPRINT_MAPPING", "")
    if mapping_json:
        import json
        try:
            return json.loads(mapping_json)
        except:
            pass
    return PROJECT_SPRINT_MAPPING
