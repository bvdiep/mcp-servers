"""
MCP Knowledge Server
Provides knowledge retrieval using Ragflow RAG

Tools:
- ragflow_query: Query knowledge base
"""
import asyncio
from typing import Any, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import RAGFLOW_API_KEY, RAGFLOW_BASE_URL
from logger import setup_server_logging
from ragflow_adapter import RagflowAdapter

# Khởi tạo logger cho server này
logger = setup_server_logging("MCP-KNOWLEDGE")

# Create MCP Server
app = Server("mcp-knowledge")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="ragflow_query",
            description="Query knowledge base using Ragflow RAG",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Question to ask"},
                    "knowledge": {
                        "type": "string",
                        "enum": ["lily", "ruatrangnguyen", "yte", "private", "company"],
                        "description": "Knowledge base to query",
                        "default": "lily"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    logger.info(f"Received tool call: {name}")
    
    if name == "ragflow_query":
        if not RAGFLOW_API_KEY or not RAGFLOW_BASE_URL:
            logger.error("RAGFLOW_API_KEY or RAGFLOW_BASE_URL not configured")
            return [TextContent(type="text", text="Error: RAGFLOW_API_KEY and RAGFLOW_BASE_URL not configured")]
        
        query = arguments.get("query")
        knowledge = arguments.get("knowledge", "lily")
        
        if not query:
            logger.warning("ragflow_query called without query")
            return [TextContent(type="text", text="Error: query required")]
        
        logger.info(f"[ragflow_query] Query: {query}, Knowledge: {knowledge}")
        
        # Map knowledge type to task type
        task_map = {
            "lily": "knowleadge_lily",
            "ruatrangnguyen": "knowleadge_ruatrangnguyen",
            "company": "knowleadge_group",
            "private": "knowleadge_private",
            "yte": "knowleadge_healthcare"
        }
        
        task_type = task_map.get(knowledge, "knowleadge_lily")
        logger.info(f"[ragflow_query] Mapped to task_type: {task_type}")
        
        try:
            logger.info(f"[ragflow_query] Calling Ragflow API with task: {task_type}")
            adapter = RagflowAdapter(RAGFLOW_API_KEY, RAGFLOW_BASE_URL)
            await adapter.init()
            result = await adapter.query(query, task_type)
            await adapter.close()
            
            answer = result.get("text", "No answer")
            references = result.get("references", [])
            
            logger.info(f"[ragflow_query] Got response with {len(references)} references")
            
            output = answer
            
            if references:
                output += "\n\n**References:**\n"
                for ref in references:
                    output += f"- {ref.get('title', 'Document')}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            logger.error(f"[ragflow_query] Error: {e}", exc_info=True)
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    logger.warning(f"Unknown tool called: {name}")
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the server"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())