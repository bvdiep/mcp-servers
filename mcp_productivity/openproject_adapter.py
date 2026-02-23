"""
OpenProject Adapter - Standalone version for MCP Productivity Server
"""
import requests
import json
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class OpenProjectStats:
    """Class for interacting with OpenProject API"""
    
    def __init__(self, api_key: str, base_url: str, project_id: int):
        self.api_key = api_key
        self.base_url = base_url
        self.project_id = project_id
        self.headers = {'Content-Type': 'application/json'}
        self.auth = ('apikey', api_key)
    
    def get_current_sprint(self) -> List[Dict[str, Any]]:
        """Get current sprint information"""
        url = f"{self.base_url}/api/v3/projects/{self.project_id}/versions"
        response = requests.get(url, headers=self.headers, auth=self.auth, params={})
        
        current_versions = []
        if response.status_code == 200:
            versions = response.json().get('_embedded', {}).get('elements', [])
            today = datetime.now(timezone.utc).date()
            
            for version in versions:
                start_str = version.get('startDate')
                end_str = version.get('endDate')
                
                start_date = parse(start_str).date() if start_str else None
                end_date = parse(end_str).date() if end_str else None
                
                if start_date and today >= start_date and (end_date is None or today <= end_date):
                    days_passed = (today - start_date).days + 1 if start_date else -1
                    days_remaining = (end_date - today).days if end_date else -1
                    
                    current_versions.append({
                        'id': version['id'],
                        'name': version['name'],
                        'start': start_date,
                        'end': end_date,
                        'days_passed': days_passed,
                        'days_remaining': days_remaining
                    })
            
            if not current_versions:
                # No current version, get the latest one
                if versions:
                    # Safely get version with highest ID
                    latest_version = max(versions, key=lambda v: int(v['id']) if str(v['id']).isdigit() else 0)
                    start_date = parse(latest_version.get('startDate')).date() if latest_version.get('startDate') else None
                    end_date = parse(latest_version.get('endDate')).date() if latest_version.get('endDate') else None
                    days_passed = (today - start_date).days + 1 if start_date else -1
                    days_remaining = (end_date - today).days if end_date else -1
                    
                    current_versions.append({
                        'id': latest_version['id'],
                        'name': latest_version['name'],
                        'start': start_date,
                        'end': end_date,
                        'days_passed': days_passed,
                        'days_remaining': days_remaining
                    })
        else:
            logger.error(f"Failed to fetch versions: {response.status_code}")
        
        return current_versions
    
    def fetch_ticket_by_filter(self, filters: List[Dict]) -> List[Dict]:
        """Fetch tickets with filters"""
        url = f"{self.base_url}/api/v3/projects/{self.project_id}/work_packages"
        params = {}
        if filters:
            params["filters"] = json.dumps(filters)
        
        response = requests.get(url, headers=self.headers, auth=self.auth, params=params)
        
        if response.status_code == 200:
            return response.json().get("_embedded", {}).get("elements", [])
        else:
            logger.error(f"Error fetching tickets: {response.status_code}")
            return []
    
    def fetch_ticket_status_counts_by_version(self, version_id: int) -> Dict[str, Any]:
        """Get ticket counts by status for a version"""
        filters = [{"version": {"operator": "=", "values": [str(version_id)]}}]
        work_packages = self.fetch_ticket_by_filter(filters)
        
        # Count by status
        status_count = defaultdict(int)
        for wp in work_packages:
            status_name = wp.get("_links", {}).get("status", {}).get("title", "Unknown")
            status_count[status_name] += 1
        
        # Summarize by assignee
        summarize = self._summarize_work_packages(work_packages)
        
        return dict(status_count), summarize, {}, {}
    
    def _summarize_work_packages(self, work_packages: List[Dict]) -> Dict[str, Dict[str, int]]:
        """Summarize work packages by assignee and status"""
        summary = defaultdict(lambda: defaultdict(int))
        
        for wp in work_packages:
            status_name = wp.get("_links", {}).get("status", {}).get("title", "Unknown")
            assignee = wp.get("_links", {}).get("assignee", {}).get("title", "Unassigned")
            
            summary[assignee][status_name] += 1
            summary[assignee]["Total"] += 1
        
        # Convert to regular dict
        return {k: dict(v) for k, v in summary.items()}
