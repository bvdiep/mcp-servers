"""
Metabase Adapter - Standalone version for MCP Media & Analytics Server
Business Intelligence and analytics queries using Metabase API
"""
import requests
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import json

logger = logging.getLogger(__name__)


class MetabaseAdapter:
    """Adapter for Metabase BI API"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "X-Api-Key": api_key
        })
    
    def query_sql(self, sql: str, database_id: int) -> Dict[str, Any]:
        """Execute SQL query"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/dataset",
                json={
                    "database": database_id,
                    "query": {"source-table": f"sql:{sql}"}
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Query failed: {response.status_code} - {response.text}")
                return {"data": {"rows": []}}
            
            return response.json()
        except Exception as e:
            logger.error(f"Metabase query error: {e}")
            return {"data": {"rows": []}}
    
    def query_native(self, query: Dict[str, Any], database_id: int) -> Dict[str, Any]:
        """Execute native query"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/dataset",
                json={
                    "database": database_id,
                    "type": "native",
                    "native": query
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Query failed: {response.status_code}")
                return {"data": {"rows": []}}
            
            return response.json()
        except Exception as e:
            logger.error(f"Metabase query error: {e}")
            return {"data": {"rows": []}}
    
    def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of databases"""
        try:
            response = self.session.get(f"{self.base_url}/api/database")
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
        except Exception as e:
            logger.error(f"Get databases error: {e}")
            return []
    
    def get_tables(self, database_id: int) -> List[Dict[str, Any]]:
        """Get tables in a database"""
        try:
            response = self.session.get(f"{self.base_url}/api/database/{database_id}/tables")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Get tables error: {e}")
            return []


def metabase_result_to_df(cols: List[str], rows: List[List], time_col: str = None) -> pd.DataFrame:
    """Convert Metabase result to DataFrame"""
    df = pd.DataFrame(rows, columns=cols)
    
    if time_col and time_col in df.columns:
        try:
            df[time_col] = pd.to_datetime(df[time_col])
        except:
            pass
    
    return df


# --- Tool Functions ---

async def check_attendance(
    bi_api_key: str,
    bi_base_url: str,
    database_id: str,
    date: str = None,
    team: str = None
) -> Dict[str, Any]:
    """Check attendance for a team"""
    if not bi_api_key or not bi_base_url:
        return {
            "type": "text",
            "text": "Chưa cấu hình BI_API_KEY và BI_BASE_URL",
            "photos": []
        }
    
    import datetime
    if not date:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Build simple SQL query for attendance
    # This is a placeholder - actual query depends on your database schema
    # Use parameterized values to prevent SQL injection
    sql = """
    SELECT username, type, date_val, time, reason
    FROM attendance
    WHERE date_val = :date
    """
    
    params = {"date": date}
    
    if team:
        sql += " AND team = :team"
        params["team"] = team
    
    try:
        adapter = MetabaseAdapter(bi_base_url, bi_api_key)
        db_id = int(database_id) if database_id else 0
        
        # For Metabase, escape values to prevent SQL injection
        safe_date = date.replace("'", "''")
        sql = f"""
        SELECT username, type, date_val, time, reason
        FROM attendance
        WHERE date_val = '{safe_date}'
        """
        
        if team:
            safe_team = team.replace("'", "''")
            sql += f" AND team = '{safe_team}'"
        
        data = adapter.query_sql(sql, db_id)
        rows = data.get("data", {}).get("rows", [])
        
        if not rows:
            return {
                "type": "text",
                "text": f"Không có người nghỉ phép hoặc remote trong ngày {date}",
                "photos": []
            }
        
        output = f"📅 Ngày {date}"
        if team:
            output += f" - Team {team}"
        output += "\n\n"
        
        for row in rows:
            username, type_val, date_val, time_val, reason = row
            type_text = "Nghỉ phép" if type_val == "/nghiphep" else "Remote"
            output += f"- {username} | {type_text} | {time_val} | {reason or ''}\n"
        
        return {
            "type": "text",
            "text": output,
            "photos": []
        }
    
    except Exception as e:
        logger.error(f"Attendance error: {e}")
        return {
            "type": "text",
            "text": f"Lỗi khi lấy dữ liệu điểm danh: {str(e)}",
            "photos": []
        }


async def get_ai_review_data(
    bi_api_key: str,
    bi_base_url: str,
    database_id: str,
    project: str = None,
    member: str = None,
    start_time: str = None,
    end_time: str = None,
    limit: int = 60
) -> Dict[str, Any]:
    """Get AI code review data"""
    if not bi_api_key or not bi_base_url:
        return {
            "type": "text",
            "text": "Chưa cấu hình BI_API_KEY và BI_BASE_URL",
            "photos": []
        }
    
    # Build query for code reviews - escape values to prevent SQL injection
    def escape_sql(s):
        return s.replace("'", "''") if s else ""
    
    sql = "SELECT pr_number, project, committer, score, pr_date FROM code_reviews WHERE 1=1"
    
    if project:
        sql += f" AND project = '{escape_sql(project)}'"
    if member:
        sql += f" AND committer = '{escape_sql(member)}'"
    if start_time:
        sql += f" AND pr_date >= '{escape_sql(start_time)}'"
    if end_time:
        sql += f" AND pr_date <= '{escape_sql(end_time)}'"
    
    # Validate limit is a positive integer
    safe_limit = min(max(int(limit) if str(limit).isdigit() else 60, 1), 1000)
    sql += f" ORDER BY pr_date DESC LIMIT {safe_limit}"
    
    try:
        adapter = MetabaseAdapter(bi_base_url, bi_api_key)
        db_id = int(database_id) if database_id else 0
        
        data = adapter.query_sql(sql, db_id)
        rows = data.get("data", {}).get("rows", [])
        
        if not rows:
            return {
                "type": "text",
                "text": "Không có dữ liệu review nào",
                "photos": []
            }
        
        output = "📊 AI Code Review\n\n"
        
        # Group by project/member
        for row in rows[:10]:
            pr_num, proj, author, score, pr_date = row
            output += f"- PR #{pr_num} | {proj} | {author} | Score: {score}\n"
        
        return {
            "type": "text",
            "text": output,
            "photos": []
        }
    
    except Exception as e:
        logger.error(f"AI Review error: {e}")
        return {
            "type": "text",
            "text": f"Lỗi khi lấy dữ liệu AI review: {str(e)}",
            "photos": []
        }


async def query_telemetry_metabase(
    bi_api_key: str,
    bi_base_url: str,
    database_id: str,
    device_id: int,
    telemetry_keys: List[str],
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """Query telemetry data from Metabase"""
    if not bi_api_key or not bi_base_url:
        return {
            "type": "text",
            "text": "Chưa cấu hình BI_API_KEY và BI_BASE_URL",
            "photos": []
        }
    
    keys_str = ", ".join(telemetry_keys)
    sql = f"""
    SELECT 
        DATE_TRUNC('hour', timestamp) as bucket_time,
        {keys_str}
    FROM telemetry
    WHERE device_id = {device_id}
      AND timestamp >= '{start_date}'
      AND timestamp <= '{end_date}'
    GROUP BY bucket_time
    ORDER BY bucket_time
    LIMIT 80
    """
    
    try:
        adapter = MetabaseAdapter(bi_base_url, bi_api_key)
        db_id = int(database_id) if database_id else 0
        
        data = adapter.query_sql(sql, db_id)
        rows = data.get("data", {}).get("rows", [])
        
        if not rows:
            return {
                "type": "text",
                "text": f"Không có dữ liệu telemetry trong khoảng thời gian",
                "photos": []
            }
        
        # Convert to DataFrame for processing
        cols = ["bucket_time"] + telemetry_keys
        df = metabase_result_to_df(cols, rows, "bucket_time")
        
        # Generate summary
        output = "📊 Dữ liệu Telemetry\n\n"
        for key in telemetry_keys:
            if key in df.columns:
                values = df[key].dropna()
                if not values.empty:
                    output += f"{key}:\n"
                    output += f"  - Số điểm: {len(values)}\n"
                    output += f"  - Min: {values.min():.1f}\n"
                    output += f"  - Max: {values.max():.1f}\n"
                    output += f"  - Avg: {values.mean():.1f}\n\n"
        
        return {
            "type": "text",
            "text": output,
            "photos": []
        }
    
    except Exception as e:
        logger.error(f"Telemetry query error: {e}")
        return {
            "type": "text",
            "text": f"Lỗi khi truy vấn telemetry: {str(e)}",
            "photos": []
        }
