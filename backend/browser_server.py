import asyncio
import logging
import base64
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, quote_plus, urljoin
import ipaddress
import re

from playwright.async_api import async_playwright, Browser, Page

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

# -------------------------
# Logging
# -------------------------
logger = logging.getLogger("browser_mcp_server")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# -------------------------
# Safety helpers
# -------------------------
def _is_ip_address(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except Exception:
        return False

def _is_private_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except Exception:
        return False

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname or ""
    if not host:
        return False
    if host in ("localhost", "127.0.0.1", "::1"):
        return False
    if _is_ip_address(host) and _is_private_ip(host):
        return False
    return True

def _normalize_link(base: str, href: str) -> Optional[str]:
    """Return absolute link or None if invalid or javascript/mailto."""
    if not href:
        return None
    href = href.strip()
    if href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
        return None
    try:
        return urljoin(base, href)
    except Exception:
        return None

# -------------------------
# Browser Manager (reuse browser to save startup time)
# -------------------------
class BrowserManager:
    def __init__(self):
        self._browser: Optional[Browser] = None
        self._playwright = None
        self._lock = asyncio.Lock()

    async def start(self):
        async with self._lock:
            if self._browser:
                return
            self._playwright = await async_playwright().__aenter__()
            self._browser = await self._playwright.chromium.launch(headless=True)

    async def stop(self):
        async with self._lock:
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    logger.debug("Error closing browser", exc_info=True)
                self._browser = None
            if self._playwright:
                try:
                    await self._playwright.__aexit__(None, None, None)
                except Exception:
                    logger.debug("Error shutting down playwright", exc_info=True)
                self._playwright = None

    async def new_page(self, user_agent: Optional[str] = None) -> Page:
        if not self._browser:
            await self.start()
        context = await self._browser.new_context(user_agent=user_agent) if user_agent else await self._browser.new_context()
        page = await context.new_page()
        return page

# single manager instance
_browser_manager = BrowserManager()

# -------------------------
# The MCP Server
# -------------------------
class BrowserMCPServer(IMCPExternalServer):
    """MCP Server providing tools for web browsing, multi-engine search, and page extraction."""

    def __init__(self):
        super().__init__(name="Browser")
        logger.info("Browser MCP Server initialized.")

    def list_tools(self) -> List[MCPTool]:
        """Return tool definitions (schemas) for discovery."""
        return [
            MCPTool(
                name="browser.perform_google_search",
                description="Perform Google search; returns top results (title + link).",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "count": {"type": "integer", "minimum": 1, "maximum": 20}},
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="browser.perform_bing_search",
                description="Perform Bing search; returns top results (title + link).",
                parameters={
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "count": {"type": "integer", "minimum": 1, "maximum": 20}},
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="browser.browse_website",
                description="Visit a URL and extract cleaned text snippet and title.",
                parameters={
                    "type": "object",
                    "properties": {"url": {"type": "string"}, "max_chars": {"type": "integer", "minimum": 100, "maximum": 10000}},
                    "required": ["url"]
                }
            ),
            MCPTool(
                name="browser.fetch_metadata",
                description="Fetch page metadata: title, meta description, open graph tags.",
                parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
            ),
            MCPTool(
                name="browser.extract_links",
                description="Extract links from the page (normalized absolute URLs).",
                parameters={"type": "object", "properties": {"url": {"type": "string"}, "max_links": {"type": "integer", "minimum": 1, "maximum": 100}}, "required": ["url"]}
            ),
            MCPTool(
                name="browser.take_screenshot",
                description="Take a PNG screenshot of the page and return Base64-encoded bytes.",
                parameters={"type": "object", "properties": {"url": {"type": "string"}, "full_page": {"type": "boolean"}}, "required": ["url"]}
            ),
            MCPTool(
                name="browser.head_request",
                description="Perform a HEAD request to check status and content-type (faster than full render).",
                parameters={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}
            ),
        ]

    async def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool calls to internal methods with schema validation (lightweight)."""
        try:
            if tool_name == "browser.perform_google_search":
                query = args.get("query")
                count = int(args.get("count", 8))
                if not query:
                    return {"error": "Query parameter required", "code": 400}
                return await self._search_google(query, count)

            if tool_name == "browser.perform_bing_search":
                query = args.get("query")
                count = int(args.get("count", 8))
                if not query:
                    return {"error": "Query parameter required", "code": 400}
                return await self._search_bing(query, count)

            if tool_name == "browser.browse_website":
                url = args.get("url")
                max_chars = int(args.get("max_chars", 3000))
                if not url:
                    return {"error": "URL parameter required", "code": 400}
                return await self._browse_page(url, max_chars)

            if tool_name == "browser.fetch_metadata":
                url = args.get("url")
                if not url:
                    return {"error": "URL parameter required", "code": 400}
                return await self._fetch_metadata(url)

            if tool_name == "browser.extract_links":
                url = args.get("url")
                max_links = int(args.get("max_links", 50))
                if not url:
                    return {"error": "URL parameter required", "code": 400}
                return await self._extract_links(url, max_links)

            if tool_name == "browser.take_screenshot":
                url = args.get("url")
                full_page = bool(args.get("full_page", True))
                if not url:
                    return {"error": "URL parameter required", "code": 400}
                return await self._take_screenshot(url, full_page)

            if tool_name == "browser.head_request":
                url = args.get("url")
                if not url:
                    return {"error": "URL parameter required", "code": 400}
                return await self._head_request(url)

            return {"error": f"Tool {tool_name} not found", "code": 404}
        except Exception as e:
            logger.exception("Tool execution failed")
            return {"error": str(e), "code": 500}

    # -------------------------
    # Search helpers
    # -------------------------
    async def _search_google(self, query: str, count: int = 8) -> Dict[str, Any]:
        safe_query = quote_plus(query)
        search_url = f"https://www.google.com/search?q={safe_query}"
        logger.info("Google search: %s", query)
        page = await _browser_manager.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            elements = await page.query_selector_all("h3")
            results: List[Dict[str, str]] = []
            for el in elements[:min(len(elements), count)]:
                try:
                    title = (await el.inner_text()).strip()
                    href = await el.evaluate("node => { const a = node.closest('a'); return a ? a.href : null }")
                    if title and href:
                        results.append({"title": title, "link": href})
                except Exception:
                    logger.debug("skipping a google h3 element", exc_info=True)
                    continue
            await page.context.close()
            return {"engine": "google", "query": query, "results": results}
        except Exception as e:
            logger.exception("Google search failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Google search failed: {str(e)}", "code": 500}

    async def _search_bing(self, query: str, count: int = 8) -> Dict[str, Any]:
        safe_query = quote_plus(query)
        search_url = f"https://www.bing.com/search?q={safe_query}"
        logger.info("Bing search: %s", query)
        page = await _browser_manager.new_page()
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            # Bing often puts titles in h2 or h3; still use closest('a') approach
            elements = await page.query_selector_all("h2, h3")
            results: List[Dict[str, str]] = []
            for el in elements[:min(len(elements), count)]:
                try:
                    title = (await el.inner_text()).strip()
                    href = await el.evaluate("node => { const a = node.closest('a'); return a ? a.href : null }")
                    if title and href:
                        results.append({"title": title, "link": href})
                except Exception:
                    logger.debug("skipping a bing element", exc_info=True)
                    continue
            await page.context.close()
            return {"engine": "bing", "query": query, "results": results}
        except Exception as e:
            logger.exception("Bing search failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Bing search failed: {str(e)}", "code": 500}

    # -------------------------
    # Page fetch & metadata
    # -------------------------
    async def _browse_page(self, url: str, max_chars: int = 3000) -> Dict[str, Any]:
        if not is_safe_url(url):
            return {"error": "URL not allowed by server policy", "code": 403}
        page = await _browser_manager.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            content = await page.inner_text("body")
            title = await page.title()
            clean = " ".join(content.split())
            if len(clean) > max_chars:
                clean = clean[:max_chars].rsplit(" ", 1)[0] + "…"
            await page.context.close()
            return {"url": url, "title": title, "content_snippet": clean}
        except Exception as e:
            logger.exception("browse_page failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Failed to load page: {str(e)}", "code": 500}

    async def _fetch_metadata(self, url: str) -> Dict[str, Any]:
        if not is_safe_url(url):
            return {"error": "URL not allowed by server policy", "code": 403}
        page = await _browser_manager.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            # Evaluate metadata on page
            title = await page.title()
            description = await page.evaluate(
                "(() => { const d = document.querySelector('meta[name=\"description\"]'); return d ? d.content : null })()"
            )
            og_props = await page.evaluate(
                """() => {
                    const out = {};
                    Array.from(document.querySelectorAll('meta[property^=\"og:\"]')).forEach(m => {
                        if (m.content && m.getAttribute('property')) out[m.getAttribute('property')] = m.content;
                    });
                    return out;
                }"""
            )
            twitter_props = await page.evaluate(
                """() => {
                    const out = {};
                    Array.from(document.querySelectorAll('meta[name^=\"twitter:\"]')).forEach(m => {
                        if (m.content && m.getAttribute('name')) out[m.getAttribute('name')] = m.content;
                    });
                    return out;
                }"""
            )
            await page.context.close()
            return {"url": url, "title": title, "description": description, "open_graph": og_props, "twitter": twitter_props}
        except Exception as e:
            logger.exception("fetch_metadata failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Failed to fetch metadata: {str(e)}", "code": 500}

    async def _extract_links(self, url: str, max_links: int = 50) -> Dict[str, Any]:
        if not is_safe_url(url):
            return {"error": "URL not allowed by server policy", "code": 403}
        page = await _browser_manager.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            anchors = await page.query_selector_all("a")
            links: List[str] = []
            base = url
            for a in anchors:
                try:
                    href = await a.get_attribute("href")
                    norm = _normalize_link(base, href)
                    if norm and norm not in links:
                        links.append(norm)
                        if len(links) >= max_links:
                            break
                except Exception:
                    continue
            await page.context.close()
            return {"url": url, "links": links}
        except Exception as e:
            logger.exception("extract_links failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Failed to extract links: {str(e)}", "code": 500}

    async def _take_screenshot(self, url: str, full_page: bool = True) -> Dict[str, Any]:
        if not is_safe_url(url):
            return {"error": "URL not allowed by server policy", "code": 403}
        page = await _browser_manager.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            img_bytes = await page.screenshot(full_page=full_page)
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            await page.context.close()
            return {"url": url, "screenshot_base64": b64}
        except Exception as e:
            logger.exception("take_screenshot failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"Failed to take screenshot: {str(e)}", "code": 500}

    async def _head_request(self, url: str) -> Dict[str, Any]:
        # Use Playwright's fetch via page to get headers; this avoids full render
        if not is_safe_url(url):
            return {"error": "URL not allowed by server policy", "code": 403}
        page = await _browser_manager.new_page()
        try:
            # Use fetch in page context to do a HEAD
            result = await page.evaluate(
                """async (u) => {
                    try {
                        const r = await fetch(u, { method: 'HEAD' });
                        return { status: r.status, ok: r.ok, headers: Array.from(r.headers.entries()) };
                    } catch (e) {
                        return { error: String(e) };
                    }
                }""",
                url
            )
            await page.context.close()
            if result.get("error"):
                return {"error": result["error"], "code": 500}
            headers = {k: v for k, v in result.get("headers", [])}
            return {"url": url, "status": result.get("status"), "ok": result.get("ok"), "headers": headers}
        except Exception as e:
            logger.exception("head_request failed")
            try:
                await page.context.close()
            except Exception:
                pass
            return {"error": f"HEAD request failed: {str(e)}", "code": 500}


# -------------------------
# Optional: graceful shutdown helper
# -------------------------
async def shutdown_browser_manager():
    try:
        await _browser_manager.stop()
    except Exception:
        logger.debug("Error stopping browser manager", exc_info=True)


# -------------------------
# Quick manual test harness (run with `python backend/browser_server.py` for quick smoke-test)
# -------------------------
if __name__ == "__main__":
    async def _smoke():
        s = BrowserMCPServer()
        # ensure playwright browser launched
        await _browser_manager.start()
        print("Testing google search...")
        print(await s.execute_tool("browser.perform_google_search", {"query": "playwright python", "count": 5}))
        print("Testing bing search...")
        print(await s.execute_tool("browser.perform_bing_search", {"query": "playwright python", "count": 5}))
        print("Testing browse website...")
        print(await s.execute_tool("browser.browse_website", {"url": "https://example.com", "max_chars": 500}))
        print("Testing fetch metadata...")
        print(await s.execute_tool("browser.fetch_metadata", {"url": "https://example.com"}))
        print("Testing extract links...")
        print(await s.execute_tool("browser.extract_links", {"url": "https://example.com", "max_links": 10}))
        print("Testing head request...")
        print(await s.execute_tool("browser.head_request", {"url": "https://example.com"}))
        # screenshot test (base64 string truncated)
        ss = await s.execute_tool("browser.take_screenshot", {"url": "https://example.com"})
        print("Screenshot length:", len(ss.get("screenshot_base64", "")) if isinstance(ss, dict) else "n/a")
        await shutdown_browser_manager()

    asyncio.run(_smoke())
