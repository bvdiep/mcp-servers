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
