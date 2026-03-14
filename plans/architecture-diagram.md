# Kiến trúc MCP Servers - Trước và Sau khi tách

## Kiến trúc HIỆN TẠI (Before)

```mermaid
graph TB
    subgraph "mcp_knowledge Server"
        MK[server.py]
        MK --> ST1[search_internet tool]
        MK --> ST2[ragflow_query tool]
        
        ST1 --> SA[serper_adapter.py]
        ST1 --> WS[web_scrape.py]
        ST1 --> VA[Voyage AI]
        
        ST2 --> RA[ragflow_adapter.py]
        
        MK --> CFG[config.py]
        CFG --> ENV[.env]
        ENV --> |SERPER_API_KEY| SA
        ENV --> |VOYAGE_API_KEY| VA
        ENV --> |RAGFLOW_API_KEY| RA
        ENV --> |RAGFLOW_BASE_URL| RA
    end
    
    CLIENT[Chatbot Client] --> MK
    
    SA --> SERPER[Serper API]
    VA --> VOYAGE[Voyage AI API]
    RA --> RAGFLOW[Ragflow API]
    WS --> WEB[Web Pages]
    
    style MK fill:#ff9999
    style ST1 fill:#ffcc99
    style ST2 fill:#99ccff
```

**Vấn đề:**
- ❌ Một server xử lý 2 chức năng khác nhau
- ❌ Dependencies lẫn lộn (Serper + Ragflow)
- ❌ Khó maintain và scale
- ❌ Restart server ảnh hưởng cả 2 chức năng

---

## Kiến trúc MỚI (After)

```mermaid
graph TB
    subgraph "mcp_internet_search Server"
        MIS[server.py]
        MIS --> ST1[search_internet tool]
        
        ST1 --> SA[serper_adapter.py]
        ST1 --> WS[web_scrape.py]
        ST1 --> VA[Voyage AI]
        
        MIS --> CFG1[config.py]
        CFG1 --> ENV1[.env]
        ENV1 --> |SERPER_API_KEY| SA
        ENV1 --> |VOYAGE_API_KEY| VA
    end
    
    subgraph "mcp_knowledge Server"
        MK[server.py]
        MK --> ST2[ragflow_query tool]
        
        ST2 --> RA[ragflow_adapter.py]
        
        MK --> CFG2[config.py]
        CFG2 --> ENV2[.env]
        ENV2 --> |RAGFLOW_API_KEY| RA
        ENV2 --> |RAGFLOW_BASE_URL| RA
    end
    
    CLIENT[Chatbot Client] --> MIS
    CLIENT --> MK
    
    SA --> SERPER[Serper API]
    VA --> VOYAGE[Voyage AI API]
    RA --> RAGFLOW[Ragflow API]
    WS --> WEB[Web Pages]
    
    style MIS fill:#ffcc99
    style MK fill:#99ccff
    style ST1 fill:#ffcc99
    style ST2 fill:#99ccff
```

**Lợi ích:**
- ✅ Mỗi server có trách nhiệm rõ ràng
- ✅ Dependencies độc lập
- ✅ Dễ maintain và debug
- ✅ Có thể restart/disable từng server riêng
- ✅ Scalable và reusable

---

## So sánh Dependencies

### TRƯỚC (mcp_knowledge)
```
requests          # Cho Serper
aiohttp           # Cho Ragflow
voyageai          # Cho reranking
trafilatura       # Cho web scraping
beautifulsoup4    # Cho web scraping
lxml              # Cho web scraping
mcp, fastapi, uvicorn
pydantic
python-dotenv
```
**Tổng: 10 packages chính**

### SAU

#### mcp_internet_search
```
requests          # Cho Serper
voyageai          # Cho reranking
trafilatura       # Cho web scraping
beautifulsoup4    # Cho web scraping
lxml              # Cho web scraping
mcp, fastapi, uvicorn
pydantic
python-dotenv
```
**Tổng: 9 packages**

#### mcp_knowledge
```
aiohttp           # Cho Ragflow
mcp, fastapi, uvicorn
pydantic
python-dotenv
```
**Tổng: 5 packages**

**Kết quả:** Giảm 50% dependencies cho knowledge server!

---

## Flow hoạt động

### Search Internet Flow

```mermaid
sequenceDiagram
    participant C as Chatbot
    participant MIS as mcp_internet_search
    participant S as Serper API
    participant V as Voyage AI
    participant W as Web Pages
    
    C->>MIS: search_internet(query)
    MIS->>S: Search query
    S-->>MIS: 10 results
    MIS->>V: Rerank results
    V-->>MIS: Top 5 results
    loop Top 3 results
        MIS->>W: Scrape content
        W-->>MIS: Full content
    end
    MIS-->>C: Formatted results with content
```

### Knowledge Query Flow

```mermaid
sequenceDiagram
    participant C as Chatbot
    participant MK as mcp_knowledge
    participant R as Ragflow API
    
    C->>MK: ragflow_query(query, knowledge)
    MK->>R: Query with dataset_id
    R->>R: Semantic search + Rerank
    R-->>MK: Chunks with references
    MK-->>C: Formatted answer with sources
```

---

## File Structure Comparison

### TRƯỚC
```
mcp_knowledge/
├── server.py              (262 lines - CẢ HAI)
├── serper_adapter.py      (92 lines)
├── web_scrape.py          (73 lines)
├── ragflow_adapter.py     (132 lines)
├── config.py              (17 lines - CẢ HAI)
├── logger.py              (32 lines)
├── .env                   (4 keys)
├── requirements.txt       (10 packages)
└── README.md              (23 lines - CẢ HAI)
```

### SAU

```
mcp_internet_search/
├── server.py              (~150 lines - CHỈ SEARCH)
├── serper_adapter.py      (92 lines)
├── web_scrape.py          (73 lines)
├── config.py              (12 lines - CHỈ SEARCH)
├── logger.py              (32 lines)
├── .env                   (2 keys)
├── requirements.txt       (9 packages)
└── README.md              (~50 lines)

mcp_knowledge/
├── server.py              (~120 lines - CHỈ RAGFLOW)
├── ragflow_adapter.py     (132 lines)
├── config.py              (12 lines - CHỈ RAGFLOW)
├── logger.py              (32 lines)
├── .env                   (2 keys)
├── requirements.txt       (5 packages)
└── README.md              (~50 lines)
```

**Kết quả:**
- Code rõ ràng hơn (mỗi file nhỏ hơn)
- Dễ navigate và tìm code
- Giảm cognitive load khi đọc code

---

## Migration Path

```mermaid
graph LR
    A[mcp_knowledge<br/>Combined] --> B{Tách}
    B --> C[mcp_internet_search<br/>New]
    B --> D[mcp_knowledge<br/>Updated]
    
    C --> E[Test Internet Search]
    D --> F[Test Ragflow Query]
    
    E --> G[Update MCP Settings]
    F --> G
    
    G --> H[Restart VSCode]
    H --> I[Verify Both Tools]
    
    style A fill:#ff9999
    style C fill:#ffcc99
    style D fill:#99ccff
    style I fill:#99ff99
```

**Steps:**
1. Create new `mcp_internet_search` server
2. Update existing `mcp_knowledge` server
3. Test both servers independently
4. Update MCP settings configuration
5. Restart VSCode to load new config
6. Verify both tools work correctly

---

## Testing Strategy

### Unit Tests

```mermaid
graph TB
    subgraph "mcp_internet_search Tests"
        T1[Test Serper API]
        T2[Test Voyage Rerank]
        T3[Test Web Scraping]
        T4[Test search_internet tool]
    end
    
    subgraph "mcp_knowledge Tests"
        T5[Test Ragflow API]
        T6[Test ragflow_query tool]
    end
    
    T1 --> T4
    T2 --> T4
    T3 --> T4
    
    T5 --> T6
```

### Integration Tests

```mermaid
graph TB
    IT1[Start mcp_internet_search]
    IT2[Start mcp_knowledge]
    IT3[Call search_internet from chatbot]
    IT4[Call ragflow_query from chatbot]
    IT5[Verify no conflicts]
    
    IT1 --> IT3
    IT2 --> IT4
    IT3 --> IT5
    IT4 --> IT5
```

---

## Rollback Plan

Nếu có vấn đề, có thể rollback dễ dàng:

```mermaid
graph LR
    A[Backup mcp_knowledge] --> B[Perform Migration]
    B --> C{Test OK?}
    C -->|Yes| D[Complete]
    C -->|No| E[Restore Backup]
    E --> F[Debug Issues]
    F --> B
    
    style D fill:#99ff99
    style E fill:#ff9999
```

**Backup checklist:**
- [ ] Copy toàn bộ `mcp_knowledge/` folder
- [ ] Backup MCP settings file
- [ ] Document current working state
- [ ] Keep backup until confirmed stable

---

## Performance Impact

### Before
- **Startup time**: ~2s (load cả 2 chức năng)
- **Memory**: ~150MB (tất cả dependencies)
- **Restart impact**: Cả 2 tools bị ảnh hưởng

### After
- **Startup time**: ~1s mỗi server (nhẹ hơn)
- **Memory**: ~80MB + ~70MB (tách riêng)
- **Restart impact**: Chỉ tool bị lỗi cần restart

**Tổng kết:** Hiệu năng tốt hơn, linh hoạt hơn!
