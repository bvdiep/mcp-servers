# MCP Meeting Minutes Server v2

MCP Server để xử lý âm thanh cuộc họp bằng Gemini Multimodal Live API với hỗ trợ transcription và speaker diarization cho tiếng Việt.

## 📋 Mục lục

- [Giới thiệu](#giới-thiệu)
- [Tính năng](#tính-năng)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Cách sử dụng](#cách-sử-dụng)
- [API Reference](#api-reference)
- [Tích hợp](#tích-hợp)
- [Định dạng audio được hỗ trợ](#định-dạng-audio-được-hỗ-trợ)
- [Troubleshooting](#troubleshooting)
- [Giới hạn](#giới-hạn)
- [Cấu trúc project](#cấu-trúc-project)
- [License](#license)

---

## 🌟 Giới thiệu

`mcp_meeting_minutes_v2` là một MCP (Model Context Protocol) Server được phát triển để xử lý âm thanh cuộc họp, sử dụng Gemini Multimodal Live API của Google. Project này cho phép transcribe (chuyển đổi giọng nói thành văn bản) và phân biệt người nói (speaker diarization) cho các file audio cuộc họp với độ chính xác cao cho tiếng Việt.

Project được xây dựng trên nền tảng MCP SDK của Anthropic, cho phép tích hợp dễ dàng với các ứng dụng AI như Claude Desktop, Telegram Bot, và các hệ thống tự động hóa khác.

---

## ✨ Tính năng

### Tính năng chính

| Tính năng | Mô tả |
|-----------|-------|
| **Transcription** | Chuyển đổi âm thanh cuộc họp thành văn bản với độ chính xác cao cho tiếng Việt |
| **Speaker Diarization** | Phân biệt và nhận diện các người nói khác nhau trong cuộc họp |
| **Thuật ngữ kỹ thuật** | Nhận diện từ lóng, thuật ngữ kỹ thuật và tên riêng |
| **Đa định dạng** | Hỗ trợ nhiều định dạng audio (MP3, WAV, M4A, FLAC, OGG, AAC, WMA) |
| **Gemini 2.5 Flash** | Sử dụng model mới nhất của Google với khả năng multimodal |

### Các tính năng bổ sung

- **Tự động chuyển đổi audio**: Tự động chuyển đổi về PCM 16-bit 16kHz mono để tối ưu cho Gemini Live API
- **Xử lý file tạm thời**: Tự động dọn dẹp file tạm sau khi xử lý
- **Logging**: Hỗ trợ logging chi tiết để debug và theo dõi
- **Error handling**: Xử lý lỗi toàn diện với thông báo rõ ràng

---

## 🖥️ Yêu cầu hệ thống

### Phần mềm bắt buộc

- **Python**: 3.8+
- **FFmpeg**: Bắt buộc cho xử lý audio (pydub phụ thuộc FFmpeg)

### Cài đặt FFmpeg

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

#### Windows

1. Tải FFmpeg từ https://ffmpeg.org/download.html
2. Giải nén và thêm vào PATH
3. Hoặc sử dụng Chocolatey: `choco install ffmpeg`

### Kiểm tra FFmpeg

```bash
ffmpeg -version
```

---

## 🚀 Cài đặt

### Bước 1: Clone và cài đặt dependencies

```bash
cd mcp_meeting_minutes_v2

# Tạo virtual environment
python3 -m venv .venv

# Kích hoạt virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 2: Cấu hình API Key

Tạo file `.env` trong thư mục gốc của project:

```env
GEMINI_API_KEY="your_gemini_api_key_here"
```

**Hướng dẫn lấy API Key:**

1. Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Đăng nhập bằng tài khoản Google
3. Tạo API key mới
4. Copy và paste vào file `.env`

### Bước 3: Kiểm tra cài đặt

```bash
# Kích hoạt virtual environment
source .venv/bin/activate  # Linux/macOS
# hoặc .venv\Scripts\activate  # Windows

# Chạy demo để kiểm tra
python demo.py
```

Nếu không có lỗi, server đã sẵn sàng sử dụng.

---

## ⚙️ Cấu hình

### Biến môi trường

| Biến | Bắt buộc | Mô tả |
|------|----------|-------|
| `GEMINI_API_KEY` | Có | API key từ Google AI Studio |

### File `.env`

Tạo file `.env` trong thư mục gối của project:

```env
# API Key cho Gemini
GEMINI_API_KEY="AIzaSy..."

# (Tùy chọn) Cấu hình logging
# LOG_LEVEL=INFO
```

### Cấu hình Claude Desktop (Optional)

Để tích hợp với Claude Desktop, thêm vào file cấu hình:

```json
{
  "mcpServers": {
    "meeting-transcriber": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_meeting_minutes_v2/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp_meeting_minutes_v2/.venv/lib/python3.x/site-packages"
      }
    }
  }
}
```

---

## 📖 Cách sử dụng

### Cách 1: Chạy Demo

```bash
# Kích hoạt virtual environment
source .venv/bin/activate

# Chạy demo
python demo.py
```

Demo sẽ:
1. Kết nối đến Gemini API
2. Transcribe file audio mẫu
3. Hiển thị kết quả
4. Lưu kết quả vào file `.txt`

### Cách 2: Sử dụng như MCP Server

Chạy server để nhận các tool calls từ MCP clients:

```bash
source .venv/bin/activate
python server.py
```

Server sẽ chạy ở chế độ stdio, chờ nhận commands từ MCP client.

### Cách 3: Tích hợp với Python code

```python
import asyncio
import sys
from pathlib import Path

# Thêm đường dẫn đến module
sys.path.insert(0, '/path/to/mcp_meeting_minutes_v2')

from server import audio_processor

async def transcribe():
    # Khởi tạo client
    await audio_processor.initialize_client()
    
    # Transcribe file audio
    result = await audio_processor.transcribe_with_live_api('/path/to/audio.mp3')
    
    # In kết quả
    print(result)

asyncio.run(transcribe())
```

---

## 📚 API Reference

### Tool: `transcribe_meeting_native`

Tool chính để transcribe file âm thanh cuộc họp.

#### Input

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|----------|-------|
| `file_path` | string | Có | Đường dẫn tuyệt đối đến file âm thanh cần transcribe |

#### Output

```json
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
    },
    {
      "speaker_id": "Speaker_2",
      "segments": [
        {
          "start_time": "00:00:10",
          "end_time": "00:00:25",
          "text": "Nội dung người nói thứ hai"
        }
      ]
    }
  ]
}
```

#### Mô tả output fields

| Field | Mô tả |
|-------|-------|
| `full_transcript` | Toàn bộ nội dung cuộc họp dưới dạng text liên tục |
| `speakers` | Mảng các đối tượng người nói |
| `speaker_id` | ID của người nói (Speaker_1, Speaker_2, ...) |
| `segments` | Các đoạn audio của người nói |
| `start_time` | Thời gian bắt đầu đoạn (định dạng HH:MM:SS) |
| `end_time` | Thời gian kết thúc đoạn (định dạng HH:MM:SS) |
| `text` | Nội dung text của đoạn audio |

---

## 🔗 Tích hợp

### Claude Desktop

Thêm vào file cấu hình Claude Desktop:

```json
{
  "mcpServers": {
    "meeting-transcriber": {
      "command": "python",
      "args": ["/absolute/path/to/mcp_meeting_minutes_v2/server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/mcp_meeting_minutes_v2/.venv/lib/python3.x/site-packages"
      }
    }
  }
}
```

### Telegram Bot

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def transcribe_audio(file_path: str):
    server_params = StdioServerParameters(
        command="python",
        args=["/path/to/mcp_meeting_minutes_v2/server.py"],
        env={
            "PYTHONPATH": "/path/to/mcp_meeting_minutes_v2/.venv/lib/python3.x/site-packages"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "transcribe_meeting_native",
                {"file_path": file_path}
            )
            
            return result.content[0].text
```

### REST API

Để tạo REST API, có thể sử dụng HTTP wrapper như:

- FastAPI + MCP gateway
- Flask + MCP server wrapper

---

## 🎵 Định dạng audio được hỗ trợ

| Định dạng | Mở rộng | Hỗ trợ |
|-----------|---------|---------|
| MP3 | .mp3 | ✅ |
| WAV | .wav | ✅ |
| M4A | .m4a | ✅ |
| FLAC | .flac | ✅ |
| OGG | .ogg | ✅ |
| AAC | .aac | ✅ |
| WMA | .wma | ✅ |

### Xử lý audio nội bộ

Audio sẽ được tự động chuyển đổi về **PCM 16-bit, 16kHz, mono** để tối ưu cho Gemini Live API.

---

## 🔧 Troubleshooting

### Lỗi "FFmpeg not found"

**Nguyên nhân**: FFmpeg chưa được cài đặt hoặc chưa có trong PATH.

**Giải pháp**:
- Cài đặt FFmpeg (xem phần Cài đặt FFmpeg)
- Kiểm tra cài đặt: `ffmpeg -version`

### Lỗi "GEMINI_API_KEY not found"

**Nguyên nhân**: API key chưa được cấu hình trong file `.env`.

**Giải pháp**:
1. Tạo file `.env` trong thư mục gốc
2. Thêm `GEMINI_API_KEY="your_api_key"`
3. Khởi động lại server

### Lỗi "File not found"

**Nguyên nhân**: Đường dẫn file audio không đúng hoặc file không tồn tại.

**Giải pháp**:
- Sử dụng đường dẫn tuyệt đối cho file audio
- Kiểm tra file có tồn tại: `ls -la /path/to/audio.mp3`
- Kiểm tra quyền đọc file

### Lỗi kết nối Gemini API

**Nguyên nhân**: Không thể kết nối đến Google API.

**Giải pháp**:
- Kiểm tra kết nối internet
- Xác nhận API key còn hạn sử dụng
- Kiểm tra quota API (1M TPM cho Live API)
- Thử sử dụng VPN nếu bị chặn

### Lỗi "JSONDecodeError"

**Nguyên nhân**: Gemini API trả về response không đúng định dạng JSON.

**Giải pháp**:
- Server sẽ tự động fallback về text thuần
- Kiểm tra log để xem chi tiết response

### Lỗi "Permission denied"

**Nguyên nhân**: Không có quyền thực thi file hoặc đọc file audio.

**Giải pháp**:
- Kiểm tra quyền file: `chmod +x server.py`
- Kiểm tra quyền đọc file audio

---

## ⚠️ Giới hạn

### Giới hạn API

| Thông số | Giới hạn |
|----------|----------|
| **Quota** | Theo giới hạn của Gemini API (thường là 15 requests/minute cho free tier) |
| **Tokens per minute (TPM)** | 1M TPM cho Live API |
| **File size** | Tối đa 20MB per file (khuyến nghị) |
| **Duration** | Tối đa 60 phút per file (khuyến nghị) |

### Giới hạn ngôn ngữ

- **Tiếng Việt**: Tối ưu hóa cho tiếng Việt với khả năng nhận diện từ lóng, thuật ngữ kỹ thuật
- **Tiếng Anh**: Hỗ trợ nhưng không tối ưu bằng tiếng Việt
- **Ngôn ngữ khác**: Có thể hoạt động nhưng không được kiểm tra

### Lưu ý khác

- Audio cần có chất lượng tối thiểu để đạt hiệu quả cao
- Tiếng ồn nền có thể ảnh hưởng đến độ chính xác
- Speaker diarization phụ thuộc vào sự khác biệt về giọng nói của người nói

---

## 📁 Cấu trúc Project

```
mcp_meeting_minutes_v2/
├── .env                      # File chứa API keys (không commit)
├── .gitignore                # Git ignore rules
├── .venv/                    # Virtual environment (không commit)
├── LICENSE                   # MIT License
├── README.md                 # Tài liệu hướng dẫn
├── requirements.txt          # Danh sách Python dependencies
├── server.py                 # MCP Server chính
└── demo.py                   # Demo script minh họa cách sử dụng
```

### Mô tả các file

| File | Mô tả |
|------|-------|
| `server.py` | MCP Server chính, xử lý transcription và speaker diarization |
| `demo.py` | Script demo minh họa cách sử dụng server |
| `requirements.txt` | Danh sách dependencies: mcp, python-dotenv, google-genai, pydub, websockets |
| `.env` | File cấu hình biến môi trường |
| `LICENSE` | Giấy phép MIT |
| `.gitignore` | Cấu hình các file/folder không commit vào git |

---

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

```
MIT License

Copyright (c) 2025 MCP Meeting Minutes Server

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/ten-tinh-nang`
3. Commit changes: `git commit -m 'Add some feature'`
4. Push và tạo Pull Request

---

## 📞 Liên hệ

- **GitHub Issues**: [Tạo issue mới](https://github.com/your-repo/issues)
- **Email**: your-email@example.com

---

## 🔗 Tham khảo

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Google AI Studio](https://aistudio.google.com/)
- [Pydub Documentation](https://github.com/jiaaro/pydub)
