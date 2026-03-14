"""
MCP Internet Search Server
Provides internet search capabilities using Serper API with Voyage AI reranking

Tools:
- search_internet: Search the web for information with content extraction
"""
import asyncio
from typing import Any, List

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import adapters
from config import SERPER_API_KEY, VOYAGE_API_KEY
from logger import setup_server_logging
from serper_adapter import SerperAdapter
from web_scrape import get_optimized_llm_input

# Import Voyage AI for reranking
import voyageai


# Domains to exclude from scraping (these sites don't return useful content)
EXCLUDED_DOMAINS = [
    'youtube.com', 'youtu.be', 'youtube-nocookie.com',
    'vimeo.com', 'dailymotion.com',
    'tiktok.com', 'instagram.com', 
    'facebook.com', 'fb.watch',
    'twitter.com', 'x.com',
    'linkedin.com', 'linkedin.ai',
    'reddit.com', 'redd.it',
    'pinterest.com', 'pin.it',
]


def is_excluded_url(url: str) -> bool:
    """Check if URL belongs to an excluded domain"""
    url_lower = url.lower()
    for domain in EXCLUDED_DOMAINS:
        if domain in url_lower:
            return True
    return False

# Khởi tạo logger cho server này
logger = setup_server_logging("MCP-INTERNET-SEARCH")

# Create MCP Server
app = Server("mcp-internet-search")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_internet",
            description="Search the web for information using Google with content extraction",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls"""
    
    logger.info(f"Received tool call: {name}")
    
    if name == "search_internet":
        if not SERPER_API_KEY:
            logger.error("SERPER_API_KEY not configured")
            return [TextContent(type="text", text="Error: SERPER_API_KEY not configured")]
        
        query = arguments.get("query")
        if not query:
            logger.warning("search_internet called without query")
            return [TextContent(type="text", text="Error: query required")]
        
        logger.info(f"[search_internet] Query: {query}")
        
        try:
            # Step 1: Call Serper API
            logger.info("[search_internet] Calling Serper API...")
            adapter = SerperAdapter(SERPER_API_KEY)
            data = adapter.search(query)
            combined_snippets, organic_results = adapter.get_organic_results(data)
            logger.info(f"[search_internet] Got {len(organic_results) if organic_results else 0} organic results")
            
            if not organic_results:
                logger.warning("[search_internet] No results found from Serper")
                return [TextContent(type="text", text="No results found")]
            
            # Filter out excluded domains (YouTube, social media, etc.)
            filtered_results = [res for res in organic_results if not is_excluded_url(res.get('link', ''))]
            
            # If all results are excluded, fall back to original results
            if not filtered_results:
                logger.warning("[search_internet] All results filtered (excluded domains), using fallback")
                filtered_results = organic_results
            else:
                logger.info(f"[search_internet] {len(filtered_results)} results after domain filtering")
            
            # Rerank results using Voyage AI
            nb_results = 5
            documents_for_rerank = [res.get('snippet', '') for res in filtered_results]
            
            try:
                # Step 2: Call Voyage AI rerank
                logger.info("[search_internet] Calling Voyage AI rerank...")
                vo = voyageai.Client(api_key=VOYAGE_API_KEY)
                reranked = vo.rerank(
                    query=query,
                    documents=documents_for_rerank,
                    model="rerank-2.5",
                    top_k=nb_results
                )
                # Get top results based on reranked indices
                top_results = [filtered_results[result.index] for result in reranked.results]
                logger.info(f"[search_internet] Reranked to top {len(top_results)} results")
            except Exception as e:
                logger.warning(f"[search_internet] Voyage rerank failed: {e}, using fallback")
                top_results = filtered_results[:nb_results]
            
            output = f"**Search Results for**: {query}\n\n"
            
            # Step 3: Download full content from top results
            logger.info("[search_internet] Starting content extraction from top results")
            successful_results = 0
            for idx, res in enumerate(top_results):
                if successful_results >= 3:
                    logger.info("[search_internet] Reached max 3 successful content extractions")
                    break
                
                title = res.get("title", "No title")
                link = res.get("link", "")
                
                logger.info(f"[search_internet] Scraping result {idx+1}: {title} ({link})")
                
                output += f"### {successful_results+1}. {title}\n"
                output += f"🔗 {link}\n"
                
                # Download and extract content using Trafilatura
                try:
                    content = get_optimized_llm_input(link)
                    # Check if content was successfully downloaded
                    if content and not content.startswith("Error:") and not content.startswith("Could not"):
                        # Limit content length to avoid too long responses
                        output += f"{content[:4000]}\n\n"
                        successful_results += 1
                        logger.info(f"[search_internet] Successfully extracted content from: {title}")
                    else:
                        output += f"(Could not extract content from this URL)\n\n"
                        logger.warning(f"[search_internet] Failed to extract content from: {link}")
                except Exception as e:
                    output += f"(Error downloading content: {str(e)})\n\n"
                    logger.error(f"[search_internet] Exception while scraping {link}: {e}")
            
            if successful_results == 0:
                output += "Could not extract content from any of the search results.\n"
                logger.warning("[search_internet] No content extracted from any result")
            else:
                logger.info(f"[search_internet] Completed: {successful_results}/{len(top_results)} contents extracted")
            
            return [TextContent(type="text", text=output)]
        except Exception as e:
            logger.error(f"[search_internet] Unexpected error: {e}", exc_info=True)
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