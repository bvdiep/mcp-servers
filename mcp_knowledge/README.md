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
RAGFLOW_SIMILARITY_THRESHOLD="0.2"  # Optional: similarity threshold (default: 0.2)
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