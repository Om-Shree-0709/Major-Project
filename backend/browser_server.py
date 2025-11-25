import asyncio
import os
from typing import Dict, Any, List
from playwright.async_api import async_playwright
# Import core structures to break the circular dependency
from mcp_core import IMCPExternalServer, MCPTool 

class BrowserMCPServer(IMCPExternalServer):
    """
    MCP Server providing tools for controlled web browsing and content retrieval.
    Uses Playwright for headless browser automation.
    """
    def __init__(self):
        super().__init__(name="Browser")
        self.loop = asyncio.get_event_loop()
        print(f"Browser MCP Server initialized. Playwright ready.")

    def list_tools(self) -> List[MCPTool]:
        """Exposes the web browsing capabilities as MCP Tools."""
        return [
            MCPTool(
                name="browser.navigate_and_get_text",
                description="Navigates to a URL and returns the entire readable text content of the page. Useful for summarization.",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to navigate to (e.g., 'https://example.com')."}
                    },
                    "required": ["url"]
                }
            ),
            MCPTool(
                name="browser.search_page_for_keyword",
                description="Navigates to a URL and checks if a specific text keyword is present on the page. Returns a snippet if found.",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "The URL to navigate to."},
                        "keyword": {"type": "string", "description": "The keyword to search for on the page (case-insensitive)."}
                    },
                    "required": ["url", "keyword"]
                }
            )
        ]

    # --- Internal Asynchronous Playwright Logic ---
    async def _navigate_and_get_text_async(self, url: str) -> str:
        """Launches browser, navigates, and extracts text content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, timeout=30000) 
            await page.wait_for_selector('body')
            
            content = await page.inner_text('body')
            await browser.close()
            return content

    async def _search_page_async(self, url: str, keyword: str) -> Dict[str, Any]:
        """Launches browser, navigates, and searches for a keyword."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto(url, timeout=30000)
            await page.wait_for_selector('body')

            text_content = await page.inner_text('body')
            
            keyword_lower = keyword.lower()
            text_lower = text_content.lower()
            is_found = keyword_lower in text_lower
            
            snippet = ""
            if is_found:
                index = text_lower.find(keyword_lower)
                start = max(0, index - 100)
                end = min(len(text_content), index + len(keyword) + 100)
                snippet = text_content[start:end].replace('\n', ' ').strip() + "..."
            
            await browser.close()
            
            return {
                "url": url, 
                "keyword": keyword, 
                "found": is_found,
                "snippet": snippet if is_found else "Keyword not found."
            }


    # --- Synchronous Interface for MCP Host ---
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the asynchronous logic synchronously via the event loop."""
        
        try:
            if tool_name == "browser.navigate_and_get_text":
                content = self.loop.run_until_complete(
                    self._navigate_and_get_text_async(args["url"])
                )
                return {"url": args["url"], "content_length": len(content), "content_snippet": content[:500] + "..."}
                
            elif tool_name == "browser.search_page_for_keyword":
                result = self.loop.run_until_complete(
                    self._search_page_async(args["url"], args["keyword"])
                )
                return result

            return {"error": f"Tool '{tool_name}' not found on Browser Server."}
        
        except Exception as e:
            return {"error": f"Browser execution failed: {e!s}", "tool": tool_name}