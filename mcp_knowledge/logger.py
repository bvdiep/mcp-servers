import logging
import sys

def setup_server_logging(server_name: str):
    """
    Cấu hình logging để đẩy log về stderr, giúp Chatbot mẹ bắt được 
    và ghi vào file log tổng (aigf.log).
    """
    # Tạo logger với tên server để dễ lọc log
    logger = logging.getLogger(server_name)
    logger.setLevel(logging.INFO)

    # Xóa các handler cũ để tránh lặp log
    if logger.hasHandlers():
        logger.handlers.clear()

    # Tạo StreamHandler trỏ vào stderr
    handler = logging.StreamHandler(sys.stderr)
    
    # Format giống hệt chatbot của bạn, thêm prefix [SERVER_NAME]
    formatter = logging.Formatter(
        f'%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    # Ngăn log bị đẩy lên root logger (tránh lặp log ra stdout)
    logger.propagate = False
    
    return logger

