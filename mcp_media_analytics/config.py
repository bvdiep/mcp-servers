"""
Configuration for MCP Media & Analytics Server
Uses environment variables for configuration
"""
import os

# Immich Configuration
IMMICH_URL = os.getenv("IMMICH_URL", "https://photo.bsmlabs.ai")
IMMICH_USERNAME = os.getenv("IMMICH_USERNAME", "")
IMMICH_PASSWORD = os.getenv("IMMICH_PASSWORD", "")
IMMICH_ALBUM_ID = os.getenv("IMMICH_ALBUM_ID", "")

# Metabase Configuration
BI_API_KEY = os.getenv("BI_API_KEY", "")
BI_BASE_URL = os.getenv("BI_BASE_URL", "https://bi.bsmlabs.ai")

# Database IDs
CODE_REVIEW_DB_ID = os.getenv("CODE_REVIEW_DB_ID", "")
BSMLABS_MYSQL_ID = os.getenv("BSMLABS_MYSQL_ID", "")
BSMLABS_POSTGRES_ID = os.getenv("BSMLABS_POSTGRES_ID", "")
