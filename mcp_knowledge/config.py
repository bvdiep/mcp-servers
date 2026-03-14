"""
Configuration for MCP Knowledge Server
Uses environment variables for configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Ragflow API
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
RAGFLOW_BASE_URL = os.getenv("RAGFLOW_BASE_URL", "https://api.ragflow.io/v1")
RAGFLOW_SIMILARITY_THRESHOLD = float(os.getenv("RAGFLOW_SIMILARITY_THRESHOLD", "0.2"))
