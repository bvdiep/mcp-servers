#!/usr/bin/env python3
"""
MCP Server cho xử lý âm thanh cuộc họp bằng Gemini Multimodal Live API
Hỗ trợ transcription và speaker diarization cho tiếng Việt
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.genai as genai
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ServerCapabilities,
    ToolsCapability,
)
from pydub import AudioSegment
from pydub.utils import make_chunks

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Khởi tạo MCP Server
server = Server("meeting-transcriber")

# Cấu hình Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY không được tìm thấy trong file .env")
    sys.exit(1)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcription_jobs.db")

# System instruction cho model
SYSTEM_INSTRUCTION = """Bạn là một chuyên gia gỡ băng tiếng Việt. Hãy nhận diện chính xác các từ lóng, thuật ngữ kỹ thuật và phân biệt các người nói dựa trên sắc thái giọng nói. 

Nhiệm vụ của bạn:
1. Transcribe chính xác nội dung tiếng Việt từ audio
2. Phân biệt các người nói khác nhau (Speaker Diarization)
3. Nhận diện thuật ngữ kỹ thuật, từ lóng, tên riêng
4. Trả về kết quả dưới dạng JSON với format:
{
    "full_transcript": "Nội dung đầy đủ của cuộc họp",
    "speakers": [
        {
            "speaker_id": "Speaker_1",
            "segments": [
                {
                    "start_time": "00:00:00",
                    "end_time": "00:00:10", 
                    "text": "Nội dung người nói"
                }
            ]
        }
    ]
}
"""


class AudioProcessor:
    """Xử lý audio và streaming tới Gemini Live API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        
    async def initialize_client(self):
        """Khởi tạo Gemini client"""
        try:
            self.client = genai.Client(api_key=self.api_key)
            logger.info("Đã khởi tạo Gemini client thành công")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo Gemini client: {e}")
            raise
    
    def prepare_audio(self, file_path: str) -> AudioSegment:
        """Chuẩn bị audio cho streaming"""
        try:
            # Load audio file
            audio = AudioSegment.from_file(file_path)
            
            # Chuyển đổi về định dạng tối ưu cho Gemini Live API
            # PCM 16-bit, 16kHz, mono
            audio = audio.set_frame_rate(16000)
            audio = audio.set_channels(1)
            audio = audio.set_sample_width(2)  # 16-bit
            
            logger.info(f"Đã chuẩn bị audio: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channel(s)")
            return audio
            
        except Exception as e:
            logger.error(f"Lỗi chuẩn bị audio: {e}")
            raise
    
    async def transcribe_with_live_api(self, file_path: str) -> Dict[str, Any]:
        """Transcribe audio sử dụng Gemini API với audio input"""
        try:
            if not self.client:
                await self.initialize_client()
            
            # Chuẩn bị audio
            audio = self.prepare_audio(file_path)
            
            # Xuất audio ra file tạm thời với định dạng WAV
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                audio.export(temp_file.name, format="wav")
                temp_audio_path = temp_file.name
            
            try:
                # Upload file audio
                uploaded_file = self.client.files.upload(
                    file=temp_audio_path
                )
                
                logger.info(f"Đã upload file audio: {uploaded_file.name}")
                
                # Tạo prompt cho transcription
                prompt = f"""
                {SYSTEM_INSTRUCTION}
                
                Hãy transcribe file audio này và phân tích speaker diarization. 
                Trả về kết quả dưới dạng JSON với format chính xác như sau:
                {{
                    "full_transcript": "Nội dung đầy đủ của cuộc họp",
                    "speakers": [
                        {{
                            "speaker_id": "Speaker_1",
                            "segments": [
                                {{
                                    "start_time": "00:00:00",
                                    "end_time": "00:00:10",
                                    "text": "Nội dung người nói"
                                }}
                            ]
                        }}
                    ]
                }}
                """
                
                # Gọi Gemini API
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[
                        prompt,
                        uploaded_file
                    ]
                )
                
                response_text = response.text
                logger.info("Đã nhận được response từ Gemini API")
                
                # Parse JSON response
                try:
                    # Tìm JSON trong response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        # Nếu không tìm thấy JSON, tạo response mặc định
                        result = {
                            "full_transcript": response_text,
                            "speakers": []
                        }
                    return result
                except json.JSONDecodeError:
                    # Nếu không parse được JSON, trả về text thuần
                    return {
                        "full_transcript": response_text,
                        "speakers": []
                    }
                    
            finally:
                # Xóa file tạm thời
                import os
                try:
                    os.unlink(temp_audio_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Lỗi trong quá trình transcribe: {e}")
            raise


# ============== SQLite Database Functions ==============

def init_db():
    """Initialize SQLite database for job tracking"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transcription_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_identity TEXT NOT NULL UNIQUE,
                    file_path TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    error_message TEXT,
                    result_file_path TEXT
                )
            """)
            # Add index for faster lookups
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_identity ON transcription_jobs(file_identity)")
            conn.commit()
        logger.info(f"Database initialized at: {DB_PATH}")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_file_identity(file_path: str) -> str:
    """Generate unique identity for file based on content hash (not mtime to avoid cache miss on copy/move)"""
    path = Path(file_path)
    stat = path.stat()
    
    # Use file content hash for stable identity (works across copy/move)
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        content_hash = hasher.hexdigest()
    except IOError as e:
        logger.warning(f"Failed to hash file {file_path}, falling back to name+size: {e}")
        content_hash = f"fallback_{stat.st_size}"
    
    # Combine: filename + size + content_hash
    identity = f"{path.name}:{stat.st_size}:{content_hash}"
    return identity


def get_result_file_path(input_file_path: str) -> str:
    """Get the result file path based on file identity (to avoid name collisions)"""
    identity = get_file_identity(input_file_path)
    # Use hash of identity for unique filename
    identity_hash = hashlib.md5(identity.encode()).hexdigest()[:12]
    
    input_path = Path(input_file_path)
    # Keep original filename in result but add hash to avoid collisions
    result_name = f"{input_path.stem}_{identity_hash}.txt"
    return str(input_path.parent / result_name)


def create_job(file_path: str) -> int:
    """Create a new transcription job in the database (or return existing job ID)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            file_identity = get_file_identity(file_path)
            result_file = get_result_file_path(file_path)
            created_at = datetime.now().isoformat()
            
            # Use INSERT OR IGNORE to handle race conditions
            # If file_identity already exists, this will be ignored
            cursor.execute("""
                INSERT OR IGNORE INTO transcription_jobs (file_identity, file_path, status, created_at, result_file_path)
                VALUES (?, ?, ?, ?, ?)
            """, (file_identity, file_path, "pending", created_at, result_file))
            
            conn.commit()
            
            # Always fetch the job ID (either newly created or existing)
            cursor.execute("""
                SELECT id FROM transcription_jobs WHERE file_identity = ?
            """, (file_identity,))
            row = cursor.fetchone()
            job_id = row[0] if row else None
        
        if job_id is None:
            raise RuntimeError(f"Failed to create or find job for {file_path}")
        return job_id
    except sqlite3.Error as e:
        logger.error(f"Failed to create job: {e}")
        raise


def update_job_status(job_id: int, status: str, error_message: str = None):
    """Update job status in database"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            if status in ["completed", "failed"]:
                completed_at = datetime.now().isoformat()
                cursor.execute("""
                    UPDATE transcription_jobs 
                    SET status = ?, completed_at = ?, error_message = ?
                    WHERE id = ?
                """, (status, completed_at, error_message, job_id))
            else:
                cursor.execute("""
                    UPDATE transcription_jobs 
                    SET status = ?
                    WHERE id = ?
                """, (status, job_id))
            
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update job status: {e}")
        raise


def get_job_by_file_path(file_path: str) -> Optional[Dict[str, Any]]:
    """Get job status by file path (using file identity)"""
    try:
        file_identity = get_file_identity(file_path)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, file_identity, file_path, status, created_at, completed_at, error_message, result_file_path
                FROM transcription_jobs
                WHERE file_identity = ?
            """, (file_identity,))
            
            row = cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Failed to get job by file path: {e}")
        return None
    
    if row:
        return {
            "id": row[0],
            "file_identity": row[1],
            "file_path": row[2],
            "status": row[3],
            "created_at": row[4],
            "completed_at": row[5],
            "error_message": row[6],
            "result_file_path": row[7]
        }
    return None


def save_result_to_file(result: Dict[str, Any], file_path: str) -> str:
    """Save result to .txt file in JSON format"""
    try:
        result_file_path = get_result_file_path(file_path)
        
        with open(result_file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Result saved to: {result_file_path}")
        return result_file_path
    except IOError as e:
        logger.error(f"Failed to save result to file: {e}")
        raise


async def process_transcription_background(file_path: str, job_id: int):
    """Background task to process transcription"""
    try:
        # Update status to processing
        update_job_status(job_id, "processing")
        logger.info(f"Starting background transcription for job {job_id}")
        
        # Perform transcription
        result = await audio_processor.transcribe_with_live_api(file_path)
        
        # Save result to file
        save_result_to_file(result, file_path)
        
        # Update status to completed
        update_job_status(job_id, "completed")
        logger.info(f"Transcription completed for job {job_id}")
        
    except Exception as e:
        logger.error(f"Transcription failed for job {job_id}: {e}")
        update_job_status(job_id, "failed", str(e))
    finally:
        # Remove task reference to prevent memory leak and "Task exception was never retrieved" warning
        running_tasks.pop(job_id, None)


def start_background_transcription(file_path: str):
    """Start background transcription task"""
    # Check if job already exists
    existing_job = get_job_by_file_path(file_path)
    
    if existing_job:
        job_id = existing_job["id"]
        # If already completed or processing, don't create new job
        if existing_job["status"] in ["completed", "processing"]:
            logger.info(f"Job already exists for {file_path} with status: {existing_job['status']}")
            return job_id
        elif existing_job["status"] == "failed":
            # Re-process failed jobs by creating new job
            logger.info(f"Previous job failed for {file_path}, creating new job")
            job_id = create_job(file_path)
    else:
        # Create new job
        job_id = create_job(file_path)
    
    # Start background task and store reference to prevent unhandled exception warning
    task = asyncio.create_task(process_transcription_background(file_path, job_id))
    running_tasks[job_id] = task
    logger.info(f"Background task started for job {job_id}")
    
    return job_id


# ============== MCP Server Tools ==============

# Khởi tạo audio processor
audio_processor = AudioProcessor(GEMINI_API_KEY)

# Store background task references to prevent "Task exception was never retrieved" warning
running_tasks: Dict[int, asyncio.Task] = {}


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """Liệt kê các tools có sẵn"""
    return ListToolsResult(
        tools=[
            Tool(
                name="transcribe_meeting_native",
                description="Transcribe file âm thanh cuộc họp sử dụng Gemini Multimodal Live API với hỗ trợ speaker diarization cho tiếng Việt. Trả về kết quả ngay lập tức nếu đã xử lý, hoặc bắt đầu xử lý nền nếu chưa.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Đường dẫn tuyệt đối đến file âm thanh cần transcribe"
                        }
                    },
                    "required": ["file_path"]
                }
            ),
            Tool(
                name="get_transcription_result",
                description="Lấy kết quả transcription từ cache. Trả về kết quả đã xử lý nếu có, hoặc trạng thái hiện tại của job.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Đường dẫn tuyệt đối đến file âm thanh gốc"
                        }
                    },
                    "required": ["file_path"]
                }
            )
        ]
    )


@server.call_tool()
async def handle_call_tool(tool_name: str, arguments: dict) -> CallToolResult:
    """Xử lý các tool calls"""
    
    if tool_name == "transcribe_meeting_native":
        try:
            # Lấy file path từ arguments
            file_path = arguments.get("file_path")
            if not file_path:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Lỗi: Thiếu tham số file_path"
                    )],
                    isError=True
                )
            
            # Kiểm tra file tồn tại
            if not Path(file_path).exists():
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=f"Lỗi: File không tồn tại: {file_path}"
                    )],
                    isError=True
                )
            
            logger.info(f"Bắt đầu transcribe file: {file_path}")
            
            # Check if result already exists
            job = get_job_by_file_path(file_path)
            
            if job and job["status"] == "completed" and job.get("result_file_path"):
                result_file = job["result_file_path"]
                if Path(result_file).exists():
                    # Return cached result
                    logger.info(f"Returning cached result for: {file_path}")
                    with open(result_file, "r", encoding="utf-8") as f:
                        result = json.load(f)
                    
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps(result, ensure_ascii=False, indent=2)
                        )]
                    )
            
            # Start background processing and return immediate acknowledgment
            file_name = Path(file_path).name
            result_file = get_result_file_path(file_path)
            job_id = start_background_transcription(file_path)
            
            acknowledgment = {
                "message": f"Tiếp nhận file {file_name}, đang xử lý...",
                "job_id": job_id,
                "status": "processing",
                "result_file": result_file
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(acknowledgment, ensure_ascii=False, indent=2)
                )]
            )
            
        except Exception as e:
            logger.error(f"Lỗi trong transcribe_meeting_native: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Lỗi: {str(e)}"
                )],
                isError=True
            )
    
    elif tool_name == "get_transcription_result":
        try:
            # Lấy file path từ arguments
            file_path = arguments.get("file_path")
            if not file_path:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="Lỗi: Thiếu tham số file_path"
                    )],
                    isError=True
                )
            
            logger.info(f"Getting transcription result for: {file_path}")
            
            # Get job from database
            job = get_job_by_file_path(file_path)
            
            if not job:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "not_found",
                            "message": "Chưa có job nào cho file này"
                        }, ensure_ascii=False, indent=2)
                    )]
                )
            
            # Check if result file exists
            if job["status"] == "completed" and job.get("result_file_path"):
                result_file = job["result_file_path"]
                if Path(result_file).exists():
                    # Return cached result
                    with open(result_file, "r", encoding="utf-8") as f:
                        result = json.load(f)
                        result["status"] = "completed"
                    
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=json.dumps(result, ensure_ascii=False, indent=2)
                        )]
                    )
            elif job["status"] == "failed":
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "failed",
                            "error_message": job["error_message"],
                            "created_at": job["created_at"],
                            "completed_at": job["completed_at"]
                        }, ensure_ascii=False, indent=2)
                    )]
                )
            elif job["status"] == "processing":
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "status": "processing",
                            "message": "Đang xử lý...",
                            "job_id": job["id"],
                            "created_at": job["created_at"]
                        }, ensure_ascii=False, indent=2)
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps({
                            "status": job["status"],
                            "job_id": job["id"],
                            "created_at": job["created_at"]
                        }, ensure_ascii=False, indent=2)
                    )]
                )
                
        except Exception as e:
            logger.error(f"Lỗi trong get_transcription_result: {e}")
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Lỗi: {str(e)}"
                )],
                isError=True
            )
    
    else:
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Tool không được hỗ trợ: {request.name}"
            )],
            isError=True
        )


async def main():
    """Chạy MCP server"""
    # Initialize database
    init_db()
    
    # Khởi tạo audio processor
    try:
        await audio_processor.initialize_client()
        logger.info("MCP Server đã sẵn sàng")
    except Exception as e:
        logger.error(f"Lỗi khởi tạo: {e}")
        sys.exit(1)
    
    # Chạy server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="meeting-transcriber",
                server_version="1.0.0",
                capabilities=ServerCapabilities(
                    tools=ToolsCapability(listChanged=False)
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
