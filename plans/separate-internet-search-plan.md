# Kế hoạch tách MCP Internet Search khỏi MCP Knowledge

## Tổng quan

Hiện tại [`mcp_knowledge/server.py`](../mcp_knowledge/server.py) đang chứa 2 chức năng:
1. **Internet Search** - Tìm kiếm thông tin trên Internet (Serper + Voyage AI rerank + Web scraping)
2. **Ragflow Query** - Tra cứu kiến thức từ knowledge base (Ragflow RAG)

**Mục tiêu**: Tách thành 2 MCP servers độc lập:
- `mcp_internet_search` - Chỉ xử lý tìm kiếm Internet
- `mcp_knowledge` - Chỉ xử lý Ragflow knowledge base

## Phân tích cấu trúc hiện tại

### Files trong mcp_knowledge/

| File | Mục đích | Thuộc về |
|------|----------|----------|
| [`server.py`](../mcp_knowledge/server.py) | Main server với 2 tools | **CẢ HAI** |
| [`serper_adapter.py`](../mcp_knowledge/serper_adapter.py) | Serper API adapter | **Internet Search** |
| [`web_scrape.py`](../mcp_knowledge/web_scrape.py) | Web scraping với Trafilatura | **Internet Search** |
| [`ragflow_adapter.py`](../mcp_knowledge/ragflow_adapter.py) | Ragflow API adapter | **Knowledge** |
| [`config.py`](../mcp_knowledge/config.py) | Config cho cả 2 | **CẢ HAI** |
| [`logger.py`](../mcp_knowledge/logger.py) | Logging utility | **SHARED** |
| [`.env`](../mcp_knowledge/.env) | Environment variables | **CẢ HAI** |
| [`requirements.txt`](../mcp_knowledge/requirements.txt) | Dependencies | **CẢ HAI** |
| [`README.md`](../mcp_knowledge/README.md) | Documentation | **CẢ HAI** |

### Dependencies phân tích

**Internet Search cần:**
- `requests` - Serper API calls
- `voyageai` - Reranking results
- `trafilatura` - Web content extraction
- `beautifulsoup4`, `lxml` - HTML parsing
- `mcp`, `fastapi`, `uvicorn` - MCP server framework
- `python-dotenv` - Environment variables

**Ragflow Knowledge cần:**
- `aiohttp` - Async HTTP cho Ragflow API
- `mcp`, `fastapi`, `uvicorn` - MCP server framework
- `python-dotenv` - Environment variables

## Cấu trúc mới

```
mcp-servers/
├── mcp_internet_search/          # MỚI - Server tìm kiếm Internet
│   ├── __init__.py
│   ├── server.py                 # Tool: search_internet
│   ├── serper_adapter.py         # Di chuyển từ mcp_knowledge
│   ├── web_scrape.py             # Di chuyển từ mcp_knowledge
│   ├── config.py                 # Config cho Serper + Voyage
│   ├── logger.py                 # Copy từ mcp_knowledge
│   ├── .env                      # SERPER_API_KEY, VOYAGE_API_KEY
│   ├── requirements.txt          # Dependencies cho internet search
│   └── README.md                 # Documentation
│
└── mcp_knowledge/                # CẬP NHẬT - Chỉ giữ Ragflow
    ├── __init__.py
    ├── server.py                 # Tool: ragflow_query (XÓA search_internet)
    ├── ragflow_adapter.py        # GIỮ NGUYÊN
    ├── config.py                 # Chỉ config Ragflow
    ├── logger.py                 # GIỮ NGUYÊN
    ├── .env                      # RAGFLOW_API_KEY, RAGFLOW_BASE_URL
    ├── requirements.txt          # Dependencies cho Ragflow
    └── README.md                 # Cập nhật documentation
```

## Chi tiết thực hiện

### Bước 1: Tạo mcp_internet_search server

#### 1.1 Tạo cấu trúc thư mục
```bash
mkdir -p mcp_internet_search
```

#### 1.2 Tạo [`__init__.py`](../mcp_internet_search/__init__.py)
```python
# MCP Internet Search Server
# This module provides internet search capabilities using Serper API

__version__ = "1.0.0"
```

#### 1.3 Copy và chỉnh sửa [`logger.py`](../mcp_internet_search/logger.py)
- Copy từ [`mcp_knowledge/logger.py`](../mcp_knowledge/logger.py)
- Không cần thay đổi gì (đây là utility chung)

#### 1.4 Di chuyển [`serper_adapter.py`](../mcp_internet_search/serper_adapter.py)
- Copy từ [`mcp_knowledge/serper_adapter.py`](../mcp_knowledge/serper_adapter.py)
- Giữ nguyên nội dung (không có dependency với Ragflow)

#### 1.5 Di chuyển [`web_scrape.py`](../mcp_internet_search/web_scrape.py)
- Copy từ [`mcp_knowledge/web_scrape.py`](../mcp_knowledge/web_scrape.py)
- Giữ nguyên nội dung (standalone utility)

#### 1.6 Tạo [`config.py`](../mcp_internet_search/config.py)
```python
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
```

#### 1.7 Tạo [`.env`](../mcp_internet_search/.env)
```env
SERPER_API_KEY="6218978d19dc32a454dd5824fe6b668301681968"
VOYAGE_API_KEY="pa-MwSXlrrIyEExBv3YjyLeq7KXk_2YTTWqwGt8bmQ9Sp_"
```

#### 1.8 Tạo [`requirements.txt`](../mcp_internet_search/requirements.txt)
```txt
# MCP Internet Search Server Dependencies

# Serper API
requests>=2.31.0

# Voyage AI (for reranking)
voyageai>=0.2.0

# Web scraping
trafilatura>=1.11.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# MCP Server
mcp>=1.0.0
fastapi>=0.109.0
uvicorn>=0.27.0

# Utilities
pydantic>=2.5.0
python-dotenv
```

#### 1.9 Tạo [`server.py`](../mcp_internet_search/server.py)
- Extract phần `search_internet` tool từ [`mcp_knowledge/server.py`](../mcp_knowledge/server.py)
- Bao gồm:
  - Import statements cho Serper, Voyage, web scraping
  - `EXCLUDED_DOMAINS` list
  - `is_excluded_url()` function
  - `search_internet` tool definition
  - `search_internet` tool handler (lines 97-195 trong file gốc)

#### 1.10 Tạo [`README.md`](../mcp_internet_search/README.md)
```markdown
# MCP Internet Search Server

Tìm kiếm thông tin trên Internet sử dụng Serper API, với reranking bằng Voyage AI và web scraping.

## Features

- **Google Search**: Tìm kiếm qua Serper API
- **Smart Reranking**: Sử dụng Voyage AI rerank-2.5 để sắp xếp kết quả theo độ liên quan
- **Content Extraction**: Tự động tải và trích xuất nội dung từ các trang web
- **Domain Filtering**: Lọc bỏ các domain không phù hợp (YouTube, social media...)

## Tools

### search_internet
Tìm kiếm thông tin trên Internet và trích xuất nội dung chi tiết.

**Parameters:**
- `query` (string, required): Từ khóa tìm kiếm

**Returns:**
- Kết quả tìm kiếm với nội dung đầy đủ từ top 3 trang web

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Tạo file `.env`:
```env
SERPER_API_KEY="your-serper-api-key"
VOYAGE_API_KEY="your-voyage-api-key"
```

## Usage

```bash
python server.py
```

## MCP Settings

Thêm vào MCP settings:
```json
{
  "mcpServers": {
    "internet-search": {
      "command": "python",
      "args": ["/path/to/mcp_internet_search/server.py"],
      "env": {
        "SERPER_API_KEY": "your-key",
        "VOYAGE_API_KEY": "your-key"
      }
    }
  }
}
```
```

### Bước 2: Cập nhật mcp_knowledge (chỉ giữ Ragflow)

#### 2.1 Cập nhật [`server.py`](../mcp_knowledge/server.py)
**Xóa:**
- Import `SerperAdapter`, `voyageai`
- Import `web_scrape`
- `EXCLUDED_DOMAINS` list
- `is_excluded_url()` function
- `search_internet` tool definition trong `list_tools()`
- Toàn bộ handler cho `search_internet` (lines 97-195)

**Giữ lại:**
- Import `RagflowAdapter`
- `ragflow_query` tool definition
- `ragflow_query` tool handler

#### 2.2 Cập nhật [`config.py`](../mcp_knowledge/config.py)
```python
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
```

**Xóa:** SERPER_API_KEY, VOYAGE_API_KEY

#### 2.3 Cập nhật [`.env`](../mcp_knowledge/.env)
```env
RAGFLOW_API_KEY="ragflow-sR-LOMdIjScX2wnpaFGXeJPGCPL4PISXqwcPdT7KQjs"
RAGFLOW_BASE_URL="https://rf.bsmlabs.io"
```

**Xóa:** SERPER_API_KEY, VOYAGE_API_KEY

#### 2.4 Cập nhật [`requirements.txt`](../mcp_knowledge/requirements.txt)
```txt
# MCP Knowledge Server Dependencies

# Ragflow API
aiohttp>=3.9.0

# MCP Server
mcp>=1.0.0
fastapi>=0.109.0
uvicorn>=0.27.0

# Utilities
pydantic>=2.5.0
python-dotenv
```

**Xóa:** requests, voyageai, trafilatura, beautifulsoup4, lxml

#### 2.5 Xóa files không cần thiết
- Xóa [`serper_adapter.py`](../mcp_knowledge/serper_adapter.py)
- Xóa [`web_scrape.py`](../mcp_knowledge/web_scrape.py)

#### 2.6 Cập nhật [`README.md`](../mcp_knowledge/README.md)
```markdown
# MCP Knowledge Server

Tra cứu kiến thức từ các knowledge bases sử dụng Ragflow RAG.

## Features

- **Knowledge Retrieval**: Tra cứu thông tin từ các knowledge bases
- **Multiple Sources**: Hỗ trợ nhiều nguồn kiến thức (Lily, Rùa Trạng Nguyên, Y tế...)
- **RAG Technology**: Sử dụng Ragflow với reranking và semantic search

## Tools

### ragflow_query
Tra cứu kiến thức từ knowledge base.

**Parameters:**
- `query` (string, required): Câu hỏi cần tra cứu
- `knowledge` (string, optional): Knowledge base cần tra cứu
  - `lily` (default): Lily knowledge base
  - `ruatrangnguyen`: Rùa Trạng Nguyên
  - `yte`: Y tế
  - `company`: Công ty
  - `private`: Cá nhân

**Returns:**
- Câu trả lời từ knowledge base với references

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Tạo file `.env`:
```env
RAGFLOW_API_KEY="your-ragflow-api-key"
RAGFLOW_BASE_URL="https://rf.bsmlabs.io"
```

## Usage

```bash
python server.py
```

## MCP Settings

Thêm vào MCP settings:
```json
{
  "mcpServers": {
    "knowledge": {
      "command": "python",
      "args": ["/path/to/mcp_knowledge/server.py"],
      "env": {
        "RAGFLOW_API_KEY": "your-key",
        "RAGFLOW_BASE_URL": "https://rf.bsmlabs.io"
      }
    }
  }
}
```
```

#### 2.7 Cập nhật [`__init__.py`](../mcp_knowledge/__init__.py)
```python
# MCP Knowledge Server
# This module provides knowledge retrieval using Ragflow RAG

__version__ = "1.0.0"
```

### Bước 3: Hướng dẫn cấu hình MCP Settings

Tạo file [`MCP_CONFIGURATION.md`](../MCP_CONFIGURATION.md) trong thư mục gốc:

```markdown
# MCP Servers Configuration Guide

## Cấu hình cho 2 servers mới

Sau khi tách, bạn sẽ có 2 MCP servers độc lập:

### 1. MCP Internet Search
**Chức năng**: Tìm kiếm thông tin trên Internet

**Cấu hình MCP Settings**:
```json
{
  "mcpServers": {
    "internet-search": {
      "command": "python",
      "args": ["/home/dd/work/diep/mcp-servers/mcp_internet_search/server.py"],
      "env": {
        "SERPER_API_KEY": "6218978d19dc32a454dd5824fe6b668301681968",
        "VOYAGE_API_KEY": "pa-MwSXlrrIyEExBv3YjyLeq7KXk_2YTTWqwGt8bmQ9Sp_",
        "PYTHONPATH": "/home/dd/work/diep/mcp-servers/mcp_internet_search"
      }
    }
  }
}
```

### 2. MCP Knowledge (Ragflow)
**Chức năng**: Tra cứu kiến thức từ knowledge bases

**Cấu hình MCP Settings**:
```json
{
  "mcpServers": {
    "knowledge": {
      "command": "python",
      "args": ["/home/dd/work/diep/mcp-servers/mcp_knowledge/server.py"],
      "env": {
        "RAGFLOW_API_KEY": "ragflow-sR-LOMdIjScX2wnpaFGXeJPGCPL4PISXqwcPdT7KQjs",
        "RAGFLOW_BASE_URL": "https://rf.bsmlabs.io",
        "PYTHONPATH": "/home/dd/work/diep/mcp-servers/mcp_knowledge"
      }
    }
  }
}
```

### Cấu hình đầy đủ (cả 2 servers)

File: `~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json`

```json
{
  "mcpServers": {
    "internet-search": {
      "command": "python",
      "args": ["/home/dd/work/diep/mcp-servers/mcp_internet_search/server.py"],
      "env": {
        "SERPER_API_KEY": "6218978d19dc32a454dd5824fe6b668301681968",
        "VOYAGE_API_KEY": "pa-MwSXlrrIyEExBv3YjyLeq7KXk_2YTTWqwGt8bmQ9Sp_",
        "PYTHONPATH": "/home/dd/work/diep/mcp-servers/mcp_internet_search"
      }
    },
    "knowledge": {
      "command": "python",
      "args": ["/home/dd/work/diep/mcp-servers/mcp_knowledge/server.py"],
      "env": {
        "RAGFLOW_API_KEY": "ragflow-sR-LOMdIjScX2wnpaFGXeJPGCPL4PISXqwcPdT7KQjs",
        "RAGFLOW_BASE_URL": "https://rf.bsmlabs.io",
        "PYTHONPATH": "/home/dd/work/diep/mcp-servers/mcp_knowledge"
      }
    }
  }
}
```

## Kiểm tra sau khi cấu hình

1. **Test Internet Search**:
   ```bash
   cd mcp_internet_search
   python server.py
   ```

2. **Test Knowledge**:
   ```bash
   cd mcp_knowledge
   python server.py
   ```

3. **Restart VSCode** để load lại MCP settings

4. **Verify tools** trong chatbot:
   - `search_internet` - từ internet-search server
   - `ragflow_query` - từ knowledge server
```

## Lợi ích của việc tách

### 1. **Separation of Concerns**
- Mỗi server có trách nhiệm rõ ràng
- Dễ maintain và debug
- Code cleaner, dễ đọc hơn

### 2. **Independent Scaling**
- Có thể restart từng server độc lập
- Không ảnh hưởng lẫn nhau khi có lỗi
- Dễ dàng disable/enable từng chức năng

### 3. **Dependency Management**
- Dependencies nhẹ hơn cho mỗi server
- Không cần install packages không dùng đến
- Giảm conflicts giữa các packages

### 4. **Configuration Clarity**
- Mỗi server có config riêng
- Dễ quản lý API keys
- Rõ ràng hơn về environment variables

### 5. **Reusability**
- Có thể reuse internet search server cho projects khác
- Có thể share knowledge server độc lập
- Dễ dàng integrate vào các hệ thống khác

## Rủi ro và cách xử lý

### Rủi ro 1: Breaking changes
**Giải pháp**: 
- Giữ nguyên tool names (`search_internet`, `ragflow_query`)
- Giữ nguyên input/output schema
- Chatbot không cần thay đổi code

### Rủi ro 2: Duplicate code (logger.py)
**Giải pháp**: 
- Chấp nhận duplicate cho utility nhỏ
- Hoặc tạo shared package sau này nếu cần

### Rủi ro 3: Configuration errors
**Giải pháp**: 
- Cung cấp hướng dẫn chi tiết
- Validate environment variables khi start server
- Clear error messages

## Timeline thực hiện

Các bước có thể thực hiện tuần tự:

1. **Tạo mcp_internet_search** (30 phút)
   - Tạo cấu trúc thư mục
   - Copy/create các files
   - Test server chạy được

2. **Cập nhật mcp_knowledge** (20 phút)
   - Xóa code không cần thiết
   - Update configs
   - Test server chạy được

3. **Cấu hình MCP settings** (10 phút)
   - Update mcp_settings.json
   - Restart VSCode
   - Test cả 2 tools

4. **Testing & Documentation** (20 phút)
   - Test search_internet tool
   - Test ragflow_query tool
   - Verify không có lỗi

**Tổng thời gian**: ~1.5 giờ

## Checklist hoàn thành

- [ ] Tạo thư mục `mcp_internet_search/`
- [ ] Tạo tất cả files cho `mcp_internet_search`
- [ ] Test `mcp_internet_search` server chạy được
- [ ] Cập nhật `mcp_knowledge/server.py`
- [ ] Cập nhật `mcp_knowledge/config.py`
- [ ] Cập nhật `mcp_knowledge/.env`
- [ ] Cập nhật `mcp_knowledge/requirements.txt`
- [ ] Xóa files không cần trong `mcp_knowledge/`
- [ ] Cập nhật `mcp_knowledge/README.md`
- [ ] Test `mcp_knowledge` server chạy được
- [ ] Cập nhật MCP settings
- [ ] Test cả 2 tools trong chatbot
- [ ] Tạo documentation (MCP_CONFIGURATION.md)
- [ ] Commit changes với clear message

## Kết luận

Việc tách MCP servers sẽ giúp:
- ✅ Code structure rõ ràng hơn
- ✅ Dễ maintain và scale
- ✅ Giảm dependencies
- ✅ Tăng tính reusability
- ✅ Không breaking changes cho chatbot

Sau khi hoàn thành, bạn sẽ có 2 MCP servers độc lập, mỗi server tập trung vào 1 chức năng cụ thể.
