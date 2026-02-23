"""
Schedule Adapter - SQLite-based local storage for MCP Productivity Server
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# Vietnam timezone
VN_TZ_OFFSET = 7


class ScheduleAdapter:
    """Adapter for managing schedules using SQLite"""
    
    def __init__(self, db_path: str = "schedules.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                user_id INTEGER,
                thread_id INTEGER,
                bot_id INTEGER,
                chat_mode TEXT,
                title TEXT NOT NULL,
                team TEXT,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                type TEXT DEFAULT 'meeting',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_schedule(self, schedule_data: Dict[str, Any]) -> tuple[Optional[int], str]:
        """Add a new schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO schedules 
                (conversation_id, user_id, thread_id, bot_id, chat_mode, title, team, description, start_time, end_time, location, type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                schedule_data.get('conversation_id'),
                schedule_data.get('user_id'),
                schedule_data.get('thread_id'),
                schedule_data.get('bot_id'),
                schedule_data.get('chat_mode'),
                schedule_data.get('title'),
                schedule_data.get('team'),
                schedule_data.get('description'),
                schedule_data.get('start_time'),
                schedule_data.get('end_time'),
                schedule_data.get('location'),
                schedule_data.get('type', 'meeting')
            ))
            
            schedule_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return schedule_id, "Success"
            
        except Exception as e:
            logger.error(f"Error adding schedule: {e}")
            conn.close()
            return None, str(e)
    
    def get_schedule_by_id(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """Get a schedule by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM schedules WHERE id = ?", (schedule_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_schedules_by_date(self, date_str: str, conversation_id: int = None, thread_id: int = None) -> List[Dict[str, Any]]:
        """Get schedules for a specific date"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM schedules WHERE date(start_time) = ?"
        params = [date_str]
        
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        if thread_id:
            query += " AND thread_id = ?"
            params.append(thread_id)
        
        query += " ORDER BY start_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_schedules_by_time_range(
        self, 
        conversation_id: int, 
        start_time: str, 
        end_time: str, 
        thread_id: int = None
    ) -> List[Dict[str, Any]]:
        """Get schedules within a time range"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM schedules WHERE start_time >= ? AND start_time <= ?"
        params = [start_time, end_time]
        
        if conversation_id:
            query += " AND conversation_id = ?"
            params.append(conversation_id)
        
        if thread_id:
            query += " AND thread_id = ?"
            params.append(thread_id)
        
        query += " ORDER BY start_time"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_schedule(self, schedule_id: int, fields: Dict[str, Any]) -> bool:
        """Update a schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for key, value in fields.items():
            set_clauses.append(f"{key} = ?")
            params.append(value)
        
        if not set_clauses:
            return False
        
        params.append(schedule_id)
        
        query = f"UPDATE schedules SET {', '.join(set_clauses)} WHERE id = ?"
        
        try:
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            conn.close()
            return False
    
    def delete_schedule(self, schedule_id: int) -> bool:
        """Delete a schedule"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            conn.close()
            return False

    def search_schedules(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search schedules by title or description"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute(
            """SELECT * FROM schedules 
               WHERE title LIKE ? OR description LIKE ? 
               ORDER BY start_time DESC LIMIT ?""",
            (search_term, search_term, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


# Helper functions

def get_vietnam_timestamp() -> str:
    """Get current timestamp in Vietnam timezone"""
    now = datetime.utcnow() + timedelta(hours=VN_TZ_OFFSET)
    return now.isoformat()


def format_attributes(schedule: Dict[str, Any]) -> str:
    """Format schedule attributes for display"""
    parts = []
    
    if schedule.get('title'):
        parts.append(f"📌 **{schedule['title']}**")
    
    if schedule.get('start_time'):
        parts.append(f"🕐 Thời gian: {schedule['start_time']}")
    
    if schedule.get('end_time'):
        parts.append(f" - {schedule['end_time']}")
    
    if schedule.get('team'):
        parts.append(f"👥 Team: {schedule['team']}")
    
    if schedule.get('location'):
        parts.append(f"📍 Địa điểm: {schedule['location']}")
    
    if schedule.get('description'):
        parts.append(f"📝 Mô tả: {schedule['description']}")
    
    return "\n".join(parts)


def get_schedules_by_week(
    schedule_adapter: ScheduleAdapter, 
    conversation_id: int, 
    date: str,
    thread_id: int = None
) -> List[Dict[str, Any]]:
    """Get schedules for a week starting from a given date"""
    dt = datetime.strptime(date, "%Y-%m-%d")
    weekday = dt.weekday()
    
    # Start of week (Monday)
    start_of_week = dt - timedelta(days=weekday)
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0)
    
    # End of week (Sunday)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    
    return schedule_adapter.get_schedules_by_time_range(
        conversation_id,
        start_of_week.isoformat(),
        end_of_week.isoformat(),
        thread_id
    )
