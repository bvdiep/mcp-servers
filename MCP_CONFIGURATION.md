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

## Lưu ý quan trọng

- **Xóa server cũ**: Có thể xóa entry `internet-search` cũ trong MCP settings nếu có
- **Tool names không đổi**: `search_internet` và `ragflow_query` vẫn giữ nguyên tên
- **No breaking changes**: Chatbot không cần thay đổi code gì
- **Independent restart**: Có thể restart từng server riêng khi cần

## Troubleshooting

### Lỗi "Module not found"
- Kiểm tra `PYTHONPATH` trong MCP settings
- Đảm bảo đường dẫn đến server.py chính xác

### Lỗi "API Key not configured"
- Kiểm tra file `.env` trong từng thư mục server
- Đảm bảo environment variables được set trong MCP settings

### Server không start
- Chạy `python server.py` trực tiếp để xem lỗi
- Kiểm tra dependencies: `pip install -r requirements.txt`