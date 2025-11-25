import os
from typing import Dict, Any, List, Optional
from github import Github, Auth
from dotenv import load_dotenv

try:
    from mcp_core import IMCPExternalServer, MCPTool 
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

load_dotenv()

class GitHubMCPServer(IMCPExternalServer):
    """MCP Server providing tools for GitHub."""
    def __init__(self):
        super().__init__(name="GitHub")
        self.pat = os.getenv("GITHUB_PAT") 
        self.g = None
        if self.pat:
            try:
                self.g = Github(auth=Auth.Token(self.pat))
                self.user = self.g.get_user()
            except Exception:
                print("GitHub Auth Failed.")

    def list_tools(self) -> List[MCPTool]:
        if not self.g: return []
        return [
            MCPTool(name="github.list_repos", description="Lists top 10 repos.", parameters={"type": "object", "properties": {}}),
            MCPTool(name="github.get_repo_contents", description="Get file content.", parameters={"type": "object", "properties": {"repo_name": {"type": "string"}, "path": {"type": "string"}}, "required": ["repo_name", "path"]}),
            # NEW TOOL
            MCPTool(name="github.get_user_info", description="Get authenticated user details.", parameters={"type": "object", "properties": {}}),
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if not self.g: return {"error": "No GitHub Access"}
        try:
            if tool_name == "github.list_repos":
                repos = [{"name": r.name, "url": r.html_url, "stars": r.stargazers_count} for r in self.user.get_repos()[:5]]
                return {"repos": repos}
            
            elif tool_name == "github.get_repo_contents":
                repo = self.g.get_repo(f"{self.user.login}/{args['repo_name']}")
                content = repo.get_contents(args['path'])
                return {"content": content.decoded_content.decode('utf-8')[:1000]}
            
            elif tool_name == "github.get_user_info":
                return {
                    "login": self.user.login,
                    "name": self.user.name,
                    "public_repos": self.user.public_repos,
                    "followers": self.user.followers
                }

            return {"error": "Tool not found"}
        except Exception as e:
            return {"error": str(e)}