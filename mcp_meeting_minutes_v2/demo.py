#!/usr/bin/env python3
"""
Demo script cho MCP Meeting Transcriber Server
Minh họa cách tích hợp với MCP client
"""

import asyncio
import json
import sys
from pathlib import Path

# Thêm thư mục hiện tại vào Python path
sys.path.insert(0, str(Path(__file__).parent))

from server import audio_processor


async def demo_transcription():
    """Demo function để minh họa transcription"""
    
    print("=== MCP Meeting Transcriber Demo ===")
    print()
    
    # Tạo file audio demo với giọng nói giả lập (silence với metadata)
    from pydub import AudioSegment
    
    # Tạo audio demo: 5 giây silence (giả lập cuộc họp)
    # demo_audio = AudioSegment.silent(duration=5000)  # 5 giây
    # demo_file = "/home/dd/Downloads/audio_hop_HMI_20260226_thuyanh_aduc.ogg"
    demo_file = "/home/dd/Downloads/20260310-training-healthcare.m4a"
    # demo_audio.export(demo_file, format="wav")
    
    # print(f"📁 Đã tạo file demo: {demo_file}")
    # print("🎤 Giả lập: Cuộc họp 5 giây (silence)")
    # print()
    
    try:
        # Khởi tạo client
        await audio_processor.initialize_client()
        print("✅ Đã kết nối Gemini API")
        
        # Thực hiện transcription
        print("🔄 Đang transcribe audio...")
        result = await audio_processor.transcribe_with_live_api(demo_file)
        
        print("📝 Kết quả transcription:")
        print("=" * 50)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("=" * 50)
        
        # Lưu kết quả vào file text cùng đường dẫn với file gốc, chỉ khác đuôi
        input_path = Path(demo_file)
        output_file = input_path.with_suffix('.txt')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Đã lưu kết quả vào: {output_file}")
        
        # Giải thích kết quả
        print()
        print("💡 Giải thích:")
        print("- full_transcript: Nội dung đầy đủ của cuộc họp")
        print("- speakers: Danh sách người nói và các đoạn của họ")
        print("- Kết quả trống là bình thường vì đây là file silence")
        print()
        print("🎯 Để test với audio thật:")
        print("1. Chuẩn bị file audio có giọng nói (.mp3, .wav, .m4a)")
        print("2. Gọi tool 'transcribe_meeting_native' với file_path")
        print("3. Nhận kết quả JSON với transcript và speaker diarization")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def show_mcp_integration():
    """Hiển thị cách tích hợp với MCP clients"""
    
    print()
    print("🔗 TÍCH HỢP VỚI MCP CLIENTS")
    print("=" * 50)
    
    print()
    print("📱 Claude Desktop:")
    print("Thêm vào claude_desktop_config.json:")
    print("""
{
  "mcpServers": {
    "meeting-transcriber": {
      "command": "python",
      "args": ["/path/to/mcp_meeting_minutes_v2/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/mcp_meeting_minutes_v2/.venv/lib/python3.x/site-packages"
      }
    }
  }
}
""")
    
    print()
    print("🤖 Telegram Bot:")
    print("Sử dụng MCP client để gọi tool:")
    print("""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def transcribe_audio(file_path: str):
    server_params = StdioServerParameters(
        command="python",
        args=["/path/to/server.py"],
        env={"PYTHONPATH": "/path/to/.venv/lib/python3.x/site-packages"}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            result = await session.call_tool(
                "transcribe_meeting_native",
                {"file_path": file_path}
            )
            
            return result.content[0].text
""")
    
    print()
    print("🌐 REST API:")
    print("Chạy MCP server qua HTTP wrapper để tạo REST API")
    
    print()
    print("📋 Available Tool:")
    print("- Name: transcribe_meeting_native")
    print("- Input: file_path (string) - Đường dẫn tuyệt đối đến file audio")
    print("- Output: JSON với full_transcript và speakers array")


async def main():
    """Main demo function"""
    
    # Demo transcription
    success = await demo_transcription()
    
    if success:
        # Hiển thị cách tích hợp
        show_mcp_integration()
        
        print()
        print("🎉 Demo hoàn thành!")
        print("📚 Xem README.md để biết thêm chi tiết")
    else:
        print("❌ Demo thất bại!")


if __name__ == "__main__":
    asyncio.run(main())