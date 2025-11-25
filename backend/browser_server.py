import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright

# FIX: Robust Import
try:
    from mcp_core import IMCPExternalServer, MCPTool 
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

class BrowserMCPServer(IMCPExternalServer):
    """MCP Server providing tools for web browsing and searching."""
    def __init__(self):
        super().__init__(name="Browser")
        self.loop = asyncio.get_event_loop()
        print(f"Browser MCP Server initialized.")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="browser.navigate_and_get_text", 
                description="Navigates to URL and returns text.", 
                parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
            ),
            MCPTool(
                name="browser.perform_google_search", 
                description="Performs a Google search and returns the top results. Use this for general questions like 'latest tech news'.", 
                parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
            )
        ]

    async def _navigate_and_get_text_async(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=60000) 
            content = await page.inner_text('body')
            await browser.close()
            return content

    async def _google_search_async(self, query: str) -> Dict[str, Any]:
        """Performs a real Google Search and extracts titles/snippets."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Go to Google
            await page.goto(f"[https://www.google.com/search?q=](https://www.google.com/search?q=){query}", timeout=60000)
            await page.wait_for_load_state("networkidle")
            
            # Extract Results (Simple scraping of search result headers)
            results = []
            elements = await page.query_selector_all('div.g')
            
            for el in elements[:5]: # Get top 5 results
                try:
                    text = await el.inner_text()
                    results.append(text.split('\n')[0]) # Just take the title/headline
                except: pass
                
            await browser.close()
            return {"query": query, "top_results": results}

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "browser.navigate_and_get_text":
                content = self.loop.run_until_complete(self._navigate_and_get_text_async(args["url"]))
                return {"content": content[:1000]} # Limit size
            
            elif tool_name == "browser.perform_google_search":
                return self.loop.run_until_complete(self._google_search_async(args["query"]))
            
            return {"error": "Tool not found"}
        except Exception as e:
            print(f"Browser Error: {e}")
            return {"error": str(e)}