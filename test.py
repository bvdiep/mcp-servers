import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_single_server(server_script_path):
    # Cấu hình tham số để chạy server (giả sử dùng Python)
    server_params = StdioServerParameters(
        command="/home/dd/python/envs/mcp_knowledge/bin/python", # Trỏ vào venv
        args=[server_script_path],
        env=None
    )

    print(f"\n--- Đang kết nối tới server: {server_script_path} ---")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Khởi tạo session
            await session.initialize()

            # 2. Liệt kê danh sách các tool mà server có
            tools = await session.list_tools()
            print(f"Các tool tìm thấy: {[t.name for t in tools.tools]}")

            if not tools.tools:
                print("Server không có tool nào!")
                return

            # 3. Gọi thử một tool cụ thể (Sửa tên tool và đối số phù hợp với code của bạn)
            first_tool_name = "search_internet"
            print(f"Đang chạy thử tool: {first_tool_name}...")
            
            # Thay đổi 'arguments' theo schema của tool bạn
            result = await session.call_tool(first_tool_name, arguments={"query": "Sử đá lưu danh"}) 
            print(f"Kết quả trả về: {result.content}")

if __name__ == "__main__":
    # Thay đường dẫn tới file main.py của server bạn muốn test
    target_server = "./mcp_internet_search/server.py"
    asyncio.run(test_single_server(target_server))