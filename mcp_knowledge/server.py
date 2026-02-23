"""
MCP Knowledge Server
Manages knowledge search (Serper + Ragflow)

Tools:
- search_internet: Search the web for information
- ragflow_query: Query knowledge base
"""
import asyncio
from typing import Any, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import SERPER_API_KEY, RAGFLOW_API_KEY, RAGFLOW_BASE_URL
from serper_adapter import SerperAdapter
from ragflow_adapter import RagflowAdapter


# Create MCP Server
app = Server("mcp-knowledge")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_internet",
            description="Search the web for information using Google",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
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
    
    if name == "search_internet":
        if not SERPER_API_KEY:
            return [TextContent(type="text", text="Error: SERPER_API_KEY not configured")]
        
        query = arguments.get("query")
        if not query:
            return [TextContent(type="text", text="Error: query required")]
        
        try:
            adapter = SerperAdapter(SERPER_API_KEY)
            data = adapter.search(query)
            combined_snippets, organic_results = adapter.get_organic_results(data)
            
            if not organic_results:
                return [TextContent(type="text", text="No results found")]
            
            output = f"**Search Results for**: {query}\n\n"
            
            # Get top 3 results with content
            for i, res in enumerate(organic_results[:3]):
                title = res.get("title", "No title")
                link = res.get("link", "")
                snippet = res.get("snippet", "")
                
                output += f"### {i+1}. {title}\n"
                output += f"🔗 {link}\n"
                output += f"{snippet}\n\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    elif name == "ragflow_query":
        if not RAGFLOW_API_KEY or not RAGFLOW_BASE_URL:
            return [TextContent(type="text", text="Error: RAGFLOW_API_KEY and RAGFLOW_BASE_URL not configured")]
        
        query = arguments.get("query")
        knowledge = arguments.get("knowledge", "lily")
        
        if not query:
            return [TextContent(type="text", text="Error: query required")]
        
        # Map knowledge type to task type
        task_map = {
            "lily": "knowleadge_lily",
            "ruatrangnguyen": "knowleadge_ruatrangnguyen",
            "company": "knowleadge_group",
            "private": "knowleadge_private",
            "yte": "knowleadge_healthcare"
        }
        
        task_type = task_map.get(knowledge, "knowleadge_lily")
        
        try:
            adapter = RagflowAdapter(RAGFLOW_API_KEY, RAGFLOW_BASE_URL)
            result = await adapter.query(query, task_type)
            
            output = result.get("answer", "No answer")
            references = result.get("references", [])
            
            if references:
                output += "\n\n**References:**\n"
                for ref in references:
                    output += f"- {ref.get('title', 'Document')}\n"
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
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
