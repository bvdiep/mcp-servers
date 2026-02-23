# MCP Media & Analytics Server

Quản lý ảnh (Immich) và phân tích dữ liệu (Metabase, AI Code Review).

## Tools

Immich)
-### Photos ( `query_photo` - Tìm ảnh nâng cao (theo người, mô tả, cảm xúc)
- `query_photo_v2` - Tìm ảnh V2 (semantic search)
- `get_photo_by_emotion` - Tìm ảnh theo cảm xúc
- `get_photo_by_description` - Tìm ảnh theo mô tả chi tiết
- `get_photo_random` - Lấy ảnh ngẫu nhiên

### Analytics (Metabase)
- `check_attendance` - Kiểm tra tình trạng điểm danh (nghỉ phép, remote)
- `ai_review_get_reviews` - Lấy dữ liệu đánh giá code (AI Code Review)

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

```bash
python server.py
```
