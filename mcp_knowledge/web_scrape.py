"""
Web scraping utilities using Trafilatura
Based on aigf/utilities/web_scrape.py
"""
import trafilatura
import re
import requests


def clean_for_llm(text):
    """
    Thực hiện các bước làm sạch hậu kỳ:
    - Chuẩn hóa khoảng trắng và ngắt dòng.
    - Loại bỏ các dòng rất ngắn (thường là nhiễu còn sót lại).
    """
    if not isinstance(text, str):
        return ""
    
    # 1. Chuẩn hóa khoảng trắng và ngắt dòng
    # Thay thế nhiều ngắt dòng liên tiếp (ví dụ: >2) bằng một ngắt dòng đơn
    text = re.sub(r'\n{2,}', '\n\n', text)
    # Loại bỏ khoảng trắng thừa ở đầu/cuối mỗi dòng
    text = '\n'.join([line.strip() for line in text.split('\n')])
    
    # 2. Loại bỏ các dòng/đoạn rất ngắn, không có nội dung
    cleaned_lines = []
    for line in text.split('\n'):
        # Giữ lại các dòng có ít nhất 5 từ hoặc dòng kết thúc bằng dấu câu (thường là câu hoàn chỉnh)
        if len(line.split()) > 5 or line.endswith(('.', '!', '?', ':', ';')):
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines).strip()


def get_optimized_llm_input(url):
    """
    Quy trình tích hợp: Tải -> Trích xuất nội dung chính (Trafilatura) -> Làm sạch hậu kỳ.
    """
    try:
        # Custom headers to avoid being blocked by websites
        # Using a common browser user-agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 1. Tải nội dung thô của trang (Trafilatura sẽ sử dụng nó để phân tích)
        # Use requests with custom headers since trafilatura.fetch_url doesn't support headers param
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        downloaded = response.text
        
        if not downloaded:
            return "Error: Could not download content from URL."
        
        # 2. Trích xuất nội dung chính đã được làm sạch
        raw_article_text = trafilatura.extract(
            downloaded,
            output_format='txt',
            include_comments=False,
            no_fallback=True,
            favor_recall=False,
        )
        
        if not raw_article_text:
            return "Could not extract main content from the article."
        
        # 3. Làm sạch hậu kỳ
        optimized_text = clean_for_llm(raw_article_text)
        
        return optimized_text

    except Exception as e:
        return f"Error processing URL: {str(e)}"
