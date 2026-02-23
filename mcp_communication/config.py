"""
Configuration for MCP Communication Server
Uses environment variables for configuration
"""
import os

# Email Configuration
EMAIL_IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.zoho.com")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")

# Weather Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
