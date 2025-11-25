import os
from typing import Dict, Any, List, Optional
from github import Github, Auth, GithubException
from dotenv import load_dotenv
# Import core structures to break the circular dependency
from backend.mcp_core import IMCPExternalServer, MCPTool 

# Load environment variables (needed here as well, in case the server is run independently)
load_dotenv()

class GitHubMCPServer(IMCPExternalServer):
    """
    MCP Server providing tools for controlled interaction with the GitHub API.
    Reads GITHUB_PAT from the environment (loaded via .env).
    """
    def __init__(self):
        super().__init__(name="GitHub")
        self.pat = os.getenv("GITHUB_PAT") 
        self.g: Optional[Github] = None
        self.user_login: str = "Unauthenticated"
        
        if not self.pat:
            print("WARNING: GITHUB_PAT not found. GitHub server initialized in limited mode (will likely fail).")
        else:
            try:
                auth = Auth.Token(self.pat)
                self.g = Github(auth=auth)
                self.user = self.g.get_user()
                self.user_login = self.user.login
                print(f"GitHub MCP Server initialized for user: {self.user_login}")
            except Exception as e:
                print(f"ERROR: GitHub authentication failed: {e!s}. Check if PAT is valid.")
                self.g = None

    def list_tools(self) -> List[MCPTool]:
        """Exposes the GitHub capabilities as MCP Tools."""
        if not self.g:
            return []
            
        return [
            MCPTool(
                name="github.list_repos",
                description="Lists the names and descriptions of the authenticated user's top 10 public and private GitHub repositories.",
                parameters={"type": "object", "properties": {}}
            ),
            MCPTool(
                name="github.get_repo_contents",
                description="Retrieves the contents of a specific file from a specified repository owned by the user.",
                parameters={
                    "type": "object",
                    "properties": {
                        "repo_name": {"type": "string", "description": "The name of the repository (e.g., 'BTech-Project')."},
                        "path": {"type": "string", "description": "The path to the file within the repository (e.g., 'src/main.py')."}
                    },
                    "required": ["repo_name", "path"]
                }
            )
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handles the execution of the requested GitHub tool."""
        if not self.g:
            return {"error": "GitHub server is not authenticated. Please ensure GITHUB_PAT is set in .env."}

        try:
            if tool_name == "github.list_repos":
                repos = []
                for repo in self.user.get_repos()[:10]:
                    repos.append({
                        "name": repo.name,
                        "description": repo.description or "No description.",
                        "is_private": repo.private,
                        "url": repo.html_url
                    })
                return {"user": self.user_login, "repos_count": len(repos), "repos": repos}

            elif tool_name == "github.get_repo_contents":
                repo_name = args.get("repo_name")
                path = args.get("path")
                
                repo = self.g.get_repo(f"{self.user_login}/{repo_name}")
                
                content_file = repo.get_contents(path)
                
                if content_file.type == 'file':
                    decoded_content = content_file.decoded_content.decode('utf-8')
                    return {
                        "repo": repo_name,
                        "path": path,
                        "sha": content_file.sha,
                        "content_length": len(decoded_content),
                        "content_snippet": decoded_content[:500] + "..."
                    }
                else:
                    return {"error": f"Path '{path}' is not a file (type is {content_file.type}).", "tool": tool_name}

            raise ValueError(f"Unknown tool: {tool_name}")

        except GithubException as e:
            return {"error": f"GitHub API Error (Status {e.status}): {e.data.get('message', 'Unknown error')}. Check your PAT permissions.", "tool": tool_name}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e!s}", "tool": tool_name}