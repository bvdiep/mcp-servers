"""
Configuration for MCP Internet Search Server
Uses environment variables for configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Serper API
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# Voyage AI (for reranking)
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")