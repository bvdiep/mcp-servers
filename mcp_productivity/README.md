# MCP Productivity Server

Quản lý dự án (OpenProject) và lịch trình (Schedule).

## Tools

### OpenProject
- `get_all_projects_overview` - Lấy tổng quan các dự án
- `get_sprint_overview` - Lấy thông tin chi tiết sprint

### Schedule
- `add_schedule` - Tạo lịch họp/milestone mới
- `get_schedules_one_day` - Xem lịch trong ngày
- `get_schedules_this_week` - Xem lịch tuần
- `search_schedules` - Tìm kiếm lịch
- `update_schedule` - Cập nhật lịch
- `delete_schedule` - Xóa lịch

## Cài đặt

```bash
pip install -r requirements.txt
```

## Sử dụng

```bash
python server.py
```
