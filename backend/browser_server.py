import asyncio
from typing import Dict, Any, List
from playwright.async_api import async_playwright
# FIX: Robust Import
try:
    from mcp_core import IMCPExternalServer, MCPTool 
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

class BrowserMCPServer(IMCPExternalServer):
    """MCP Server providing tools for web browsing."""
    def __init__(self):
        super().__init__(name="Browser")
        self.loop = asyncio.get_event_loop()
        print(f"Browser MCP Server initialized.")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(name="browser.navigate_and_get_text", description="Navigates to URL and returns text.", parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}),
            MCPTool(name="browser.search_page_for_keyword", description="Searches page for keyword.", parameters={"type": "object", "properties": {"url": {"type": "string"}, "keyword": {"type": "string"}}, "required": ["url", "keyword"]})
        ]

    async def _navigate_and_get_text_async(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000) 
            content = await page.inner_text('body')
            await browser.close()
            return content

    async def _search_page_async(self, url: str, keyword: str) -> Dict[str, Any]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            text = await page.inner_text('body')
            await browser.close()
            return {"found": keyword.lower() in text.lower(), "snippet": text[:200]}

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "browser.navigate_and_get_text":
                content = self.loop.run_until_complete(self._navigate_and_get_text_async(args["url"]))
                return {"content": content[:500]}
            elif tool_name == "browser.search_page_for_keyword":
                return self.loop.run_until_complete(self._search_page_async(args["url"], args["keyword"]))
            return {"error": "Tool not found"}
        except Exception as e:
            return {"error": str(e)}