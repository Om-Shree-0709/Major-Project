import logging
import os
from typing import Dict, Any, List
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

logger = logging.getLogger("browser_mcp_server")
logger.setLevel(logging.INFO)

class BrowserMCPServer(IMCPExternalServer):
    """Browser MCP Server - Simple web search and browsing using requests."""
    
    def __init__(self):
        super().__init__(name="browser")
        logger.info("Browser MCP Server initialized (HTTP requests mode)")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="browser.search_web",
                description="Search the web and return top results",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string", 
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="browser.browse_website",
                description="Visit a URL and extract text content",
                parameters={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to visit"
                        }
                    },
                    "required": ["url"]
                }
            )
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute browser tools synchronously."""
        
        if tool_name == "browser.search_web":
            return self._search_web(args.get("query", ""))
        
        if tool_name == "browser.browse_website":
            return self._browse_page(args.get("url", ""))
            
        return {"error": f"Tool {tool_name} not found", "code": 404}

    def _search_web(self, query: str) -> Dict[str, Any]:
        """
        Simple web search using DuckDuckGo HTML.
        Fast and no API key needed.
        """
        if not query or not query.strip():
            return {"error": "Query cannot be empty", "code": 400}
        
        try:
            # Use DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result', limit=5)
            
            for div in result_divs:
                title_elem = div.find('a', class_='result__a')
                snippet_elem = div.find('a', class_='result__snippet')
                
                if title_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
            
            return {
                "query": query,
                "results": results,
                "count": len(results),
                "code": 200
            }
            
        except requests.Timeout:
            logger.error(f"Search timeout for query: {query}")
            return {"error": "Search request timed out", "code": 408}
        except Exception as e:
            logger.exception(f"Search error: {e}")
            return {"error": str(e), "code": 500}

    def _browse_page(self, url: str) -> Dict[str, Any]:
        """
        Visit a URL and extract text content using requests + BeautifulSoup.
        """
        if not url or not url.strip():
            return {"error": "URL cannot be empty", "code": 400}
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Get title
            title = soup.title.string if soup.title else "No title"
            
            # Limit content length
            max_chars = 3000
            if len(text) > max_chars:
                text = text[:max_chars] + "...[truncated]"
            
            return {
                "url": url,
                "title": title,
                "content": text,
                "length": len(text),
                "code": 200
            }
            
        except requests.Timeout:
            logger.error(f"Browse timeout for URL: {url}")
            return {"error": "Page request timed out", "url": url, "code": 408}
        except Exception as e:
            logger.exception(f"Browse error: {e}")
            return {"error": str(e), "url": url, "code": 500}
