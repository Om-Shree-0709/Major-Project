import os
import logging
import base64
import json
import time
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

# PyGithub imports (optional but recommended)
try:
    from github import Github, Auth, GithubException, InputGitAuthor
    HAVE_PYGITHUB = True
except Exception:
    HAVE_PYGITHUB = False

import requests

# mcp_core import (robust)
try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

load_dotenv()

# --- Configuration & Logging ---
logger = logging.getLogger("github_mcp_server")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

GITHUB_PAT_ENV = "GITHUB_PAT"
GITHUB_API_URL = "https://api.github.com"

# --- Helpers ---


def _get_token_from_args_or_env(args: Dict[str, Any]) -> Optional[str]:
    token = None
    if isinstance(args, dict):
        token = args.get("github_token")
    if token:
        return token
    return os.getenv(GITHUB_PAT_ENV)


def _validate_repo_full_name(repo_full_name: str) -> bool:
    return isinstance(repo_full_name, str) and "/" in repo_full_name and len(repo_full_name.split("/", 1)[0].strip()) > 0 and len(
        repo_full_name.split("/", 1)[1].strip()) > 0


def _safe_path_check(path: str) -> bool:
    if not isinstance(path, str) or path.strip() == "":
        return False
    if path.startswith("/") or "\\" in path:
        return False
    if ".." in path.split("/"):
        return False
    return True


def _base_response(code: int, data: Any = None, error: Optional[str] = None) -> Dict[str, Any]:
    if code >= 400:
        return {"code": code, "error": error}
    return {"code": code, "result": data}


def _github_client_from_token(token: str):
    if not token:
        raise ValueError("GitHub token required")
    if HAVE_PYGITHUB:
        # prefer new Auth API if available
        try:
            auth = Auth.Token(token)
            return Github(auth=auth)
        except Exception:
            return Github(token)
    else:
        session = requests.Session()
        session.headers.update({"Authorization": f"token {token}", "Accept": "application/vnd.github+json"})
        return session


def _get_rate_limit_info(client) -> Dict[str, Any]:
    try:
        if HAVE_PYGITHUB and isinstance(client, Github):
            rl = client.get_rate_limit()
            core = rl.core
            search = rl.search
            return {
                "core": {"limit": core.limit, "remaining": core.remaining, "reset": int(core.reset.timestamp())},
                "search": {"limit": search.limit, "remaining": search.remaining, "reset": int(search.reset.timestamp())},
            }
        else:
            resp = client.get(f"{GITHUB_API_URL}/rate_limit")
            resp.raise_for_status()
            data = resp.json()
            out = {}
            for k, v in data.get("resources", {}).items():
                out[k] = {"limit": v.get("limit"), "remaining": v.get("remaining"), "reset": v.get("reset")}
            return out
    except Exception as e:
        logger.debug("Failed to get rate limit: %s", e, exc_info=True)
        return {"error": str(e)}


def _extract_error_from_requests(resp: requests.Response) -> str:
    try:
        j = resp.json()
        if isinstance(j, dict) and "message" in j:
            return j["message"]
        return resp.text
    except Exception:
        return resp.text


# --- Server ---


class GitHubMCPServer(IMCPExternalServer):
    """MCP Server exposing GitHub operations."""

    def __init__(self):
        super().__init__(name="GitHub")
        self._token_env = os.getenv(GITHUB_PAT_ENV)
        self._client = None
        self._user = None
        if HAVE_PYGITHUB and self._token_env:
            try:
                logger.info("Initializing PyGithub client from environment token.")
                self._client = _github_client_from_token(self._token_env)
                try:
                    self._user = self._client.get_user()
                    logger.info("Authenticated as GitHub user: %s", getattr(self._user, "login", "unknown"))
                except Exception:
                    # user may be None for tokens with limited scopes; leave _user None
                    logger.debug("Could not fetch user info during init (token may have limited scopes).")
                    self._user = None
            except Exception:
                logger.exception("Failed to initialize PyGithub client from env token.")
                self._client = None
        else:
            if not HAVE_PYGITHUB:
                logger.warning("PyGithub not installed — server will use REST fallback. Install PyGithub for best experience.")
            if not self._token_env:
                logger.info("No GITHUB_PAT found in environment. Tools will accept per-call github_token.")

    def list_tools(self) -> List[MCPTool]:
        """Advertise available tools and parameter schemas for discovery."""
        return [
            MCPTool(name="github.rate_limit", description="Return current GitHub API rate limit info.", parameters={"type": "object", "properties": {"github_token": {"type": "string"}}}),
            MCPTool(name="github.list_repos", description="List repositories for the authenticated user or a given owner.", parameters={"type": "object", "properties": {"owner": {"type": "string"}, "limit": {"type": "integer"}, "github_token": {"type": "string"}}}),
            MCPTool(name="github.get_repo", description="Get repo metadata (owner/repo).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name"]}),
            MCPTool(name="github.read_file", description="Read a file from a repo at optional ref.", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "path": {"type": "string"}, "ref": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "path"]}),
            MCPTool(name="github.create_or_update_file", description="Create or update a file in a repo. Provide commit_message, path, content, optional branch/author.", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "path": {"type": "string"}, "content": {"type": "string"}, "commit_message": {"type": "string"}, "branch": {"type": "string"}, "author_name": {"type": "string"}, "author_email": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "path", "content", "commit_message"]}),
            MCPTool(name="github.delete_file", description="Delete a file in a repo (provide commit_message).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "path": {"type": "string"}, "commit_message": {"type": "string"}, "branch": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "path", "commit_message"]}),
            MCPTool(name="github.list_branches", description="List branches for a repo.", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name"]}),
            MCPTool(name="github.create_branch", description="Create a branch from a base branch or commit SHA.", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "new_branch": {"type": "string"}, "base": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "new_branch", "base"]}),
            MCPTool(name="github.list_issues", description="List issues in a repo (state=open/closed/all).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "state": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name"]}),
            MCPTool(name="github.create_issue", description="Create an issue (title, body, labels optional).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "labels": {"type": "array"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "title"]}),
            MCPTool(name="github.create_pull_request", description="Create a PR (head branch, base branch, title required).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "head": {"type": "string"}, "base": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "github_token": {"type": "string"}}, "required": ["repo_full_name", "head", "base", "title"]}),
            MCPTool(name="github.get_commits", description="List recent commits on a branch or sha (count optional).", parameters={"type": "object", "properties": {"repo_full_name": {"type": "string"}, "sha": {"type": "string"}, "count": {"type": "integer"}, "github_token": {"type": "string"}}, "required": ["repo_full_name"]}),
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        # Accept per-call token but fallback to env token
        token = _get_token_from_args_or_env(args) or self._token_env
        if not token:
            return _base_response(401, error="GitHub token not provided. Set GITHUB_PAT or pass github_token in args.")

        client = _github_client_from_token(token)

        # ROUTING
        try:
            if tool_name == "github.rate_limit":
                try:
                    rl = _get_rate_limit_info(client)
                    return _base_response(200, rl)
                except Exception as e:
                    logger.exception("rate_limit failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.list_repos":
                owner = args.get("owner")
                limit = int(args.get("limit", 30))
                try:
                    out = []
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        if owner:
                            try:
                                user_or_org = client.get_user(owner)
                            except GithubException:
                                user_or_org = client.get_organization(owner)
                            repos_iter = user_or_org.get_repos()
                        else:
                            user = client.get_user()
                            repos_iter = user.get_repos()
                        for i, r in enumerate(repos_iter):
                            out.append({"full_name": r.full_name, "private": r.private, "url": r.html_url, "description": r.description})
                            if i + 1 >= limit:
                                break
                    else:
                        # REST fallback
                        if owner:
                            resp = client.get(f"{GITHUB_API_URL}/users/{owner}/repos", params={"per_page": limit})
                        else:
                            resp = client.get(f"{GITHUB_API_URL}/user/repos", params={"per_page": limit})
                        resp.raise_for_status()
                        for r in resp.json():
                            out.append({"full_name": r.get("full_name"), "private": r.get("private"), "url": r.get("html_url"), "description": r.get("description")})
                    return _base_response(200, out)
                except Exception as e:
                    logger.exception("list_repos failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.get_repo":
                repo_full = args.get("repo_full_name")
                if not _validate_repo_full_name(repo_full):
                    return _base_response(400, error="repo_full_name must be 'owner/repo'")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        r = client.get_repo(repo_full)
                        data = {"full_name": r.full_name, "private": r.private, "url": r.html_url, "default_branch": r.default_branch, "description": r.description}
                    else:
                        resp = client.get(f"{GITHUB_API_URL}/repos/{repo_full}")
                        resp.raise_for_status()
                        j = resp.json()
                        data = {"full_name": j.get("full_name"), "private": j.get("private"), "url": j.get("html_url"), "default_branch": j.get("default_branch"), "description": j.get("description")}
                    return _base_response(200, data)
                except GithubException as ge:
                    logger.exception("get_repo failed (pygithub)")
                    return _base_response(getattr(ge, "status", 500), error=str(ge))
                except Exception as e:
                    logger.exception("get_repo failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.read_file":
                repo_full = args.get("repo_full_name")
                path = args.get("path")
                ref = args.get("ref", None)
                if not _validate_repo_full_name(repo_full) or not _safe_path_check(path):
                    return _base_response(400, error="Invalid repo_full_name or path")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        content_file = repo.get_contents(path, ref=ref) if ref else repo.get_contents(path)
                        raw = base64.b64decode(content_file.content).decode("utf-8", errors="replace")
                        return _base_response(200, {"path": path, "ref": content_file.sha, "content": raw})
                    else:
                        params = {}
                        if ref:
                            params["ref"] = ref
                        resp = client.get(f"{GITHUB_API_URL}/repos/{repo_full}/contents/{path}", params=params)
                        if resp.status_code == 404:
                            return _base_response(404, error="File not found")
                        resp.raise_for_status()
                        j = resp.json()
                        raw = base64.b64decode(j.get("content", "")).decode("utf-8", errors="replace")
                        return _base_response(200, {"path": path, "ref": j.get("sha"), "content": raw})
                except GithubException as ge:
                    logger.exception("read_file failed (pygithub)")
                    status = getattr(ge, "status", 500)
                    msg = str(ge.data if hasattr(ge, "data") else ge)
                    return _base_response(status, error=msg)
                except Exception as e:
                    logger.exception("read_file failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.create_or_update_file":
                repo_full = args.get("repo_full_name")
                path = args.get("path")
                content = args.get("content")
                message = args.get("commit_message")
                branch = args.get("branch", None)
                author_name = args.get("author_name")
                author_email = args.get("author_email")
                if not _validate_repo_full_name(repo_full) or not _safe_path_check(path) or not isinstance(content, str) or not message:
                    return _base_response(400, error="Invalid arguments")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        try:
                            existing = repo.get_contents(path, ref=branch) if branch else repo.get_contents(path)
                            # update
                            author = InputGitAuthor(author_name, author_email) if author_name and author_email else None
                            if author:
                                updated = repo.update_file(path, message, content, existing.sha, branch=branch, author=author)
                            else:
                                updated = repo.update_file(path, message, content, existing.sha, branch=branch)
                            return _base_response(200, {"action": "updated", "commit": updated["commit"].sha, "path": path})
                        except GithubException as ge_inner:
                            if getattr(ge_inner, "status", None) == 404:
                                # create
                                author = InputGitAuthor(author_name, author_email) if author_name and author_email else None
                                if author:
                                    created = repo.create_file(path, message, content, branch=branch, author=author)
                                else:
                                    created = repo.create_file(path, message, content, branch=branch)
                                return _base_response(201, {"action": "created", "commit": created["commit"].sha, "path": path})
                            else:
                                raise
                    else:
                        # REST fallback
                        url = f"{GITHUB_API_URL}/repos/{repo_full}/contents/{path}"
                        params = {}
                        if branch:
                            params["branch"] = branch
                        get_resp = client.get(url, params=params)
                        payload = {"message": message, "content": base64.b64encode(content.encode("utf-8")).decode("utf-8")}
                        if branch:
                            payload["branch"] = branch
                        if get_resp.status_code == 404:
                            # create
                            post_resp = client.put(url, json=payload)
                            post_resp.raise_for_status()
                            return _base_response(201, {"action": "created", "commit": post_resp.json().get("commit", {}).get("sha")})
                        else:
                            get_resp.raise_for_status()
                            existing = get_resp.json()
                            payload["sha"] = existing.get("sha")
                            put_resp = client.put(url, json=payload)
                            put_resp.raise_for_status()
                            return _base_response(200, {"action": "updated", "commit": put_resp.json().get("commit", {}).get("sha")})
                except GithubException as ge:
                    logger.exception("create_or_update_file failed (pygithub)")
                    return _base_response(getattr(ge, "status", 500), error=str(ge))
                except Exception as e:
                    logger.exception("create_or_update_file failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.delete_file":
                repo_full = args.get("repo_full_name")
                path = args.get("path")
                message = args.get("commit_message")
                branch = args.get("branch", None)
                if not _validate_repo_full_name(repo_full) or not _safe_path_check(path) or not message:
                    return _base_response(400, error="Invalid arguments")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        existing = repo.get_contents(path, ref=branch) if branch else repo.get_contents(path)
                        deleted = repo.delete_file(path, message, existing.sha, branch=branch)
                        return _base_response(200, {"action": "deleted", "commit": deleted["commit"].sha, "path": path})
                    else:
                        # REST: need sha of file
                        url = f"{GITHUB_API_URL}/repos/{repo_full}/contents/{path}"
                        params = {}
                        if branch:
                            params["ref"] = branch
                        get_resp = client.get(url, params=params)
                        if get_resp.status_code == 404:
                            return _base_response(404, error="File not found")
                        get_resp.raise_for_status()
                        existing = get_resp.json()
                        payload = {"message": message, "sha": existing.get("sha")}
                        if branch:
                            payload["branch"] = branch
                        resp = client.delete(url, json=payload)
                        resp.raise_for_status()
                        return _base_response(200, {"action": "deleted", "path": path, "commit": resp.json().get("commit", {}).get("sha")})
                except GithubException as ge:
                    logger.exception("delete_file failed (pygithub)")
                    return _base_response(getattr(ge, "status", 500), error=str(ge))
                except Exception as e:
                    logger.exception("delete_file failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.list_branches":
                repo_full = args.get("repo_full_name")
                if not _validate_repo_full_name(repo_full):
                    return _base_response(400, error="repo_full_name required")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        branches = [{"name": b.name, "commit_sha": b.commit.sha} for b in repo.get_branches()]
                    else:
                        resp = client.get(f"{GITHUB_API_URL}/repos/{repo_full}/branches")
                        resp.raise_for_status()
                        branches = [{"name": b.get("name"), "commit_sha": b.get("commit", {}).get("sha")} for b in resp.json()]
                    return _base_response(200, branches)
                except Exception as e:
                    logger.exception("list_branches failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.create_branch":
                repo_full = args.get("repo_full_name")
                new_branch = args.get("new_branch")
                base = args.get("base")
                if not _validate_repo_full_name(repo_full) or not new_branch or not base:
                    return _base_response(400, error="repo_full_name, new_branch and base required")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        # try to resolve base as branch first
                        try:
                            base_ref = repo.get_branch(base)
                            base_sha = base_ref.commit.sha
                        except GithubException:
                            # maybe a commit sha
                            base_sha = base
                        ref = f"refs/heads/{new_branch}"
                        repo.create_git_ref(ref, base_sha)
                        return _base_response(201, {"branch": new_branch, "base_sha": base_sha})
                    else:
                        # REST fallback
                        br = client.get(f"{GITHUB_API_URL}/repos/{repo_full}/git/refs/heads/{base}")
                        if br.status_code == 404:
                            base_sha = base
                        else:
                            br.raise_for_status()
                            base_sha = br.json().get("object", {}).get("sha")
                        payload = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
                        post = client.post(f"{GITHUB_API_URL}/repos/{repo_full}/git/refs", json=payload)
                        post.raise_for_status()
                        return _base_response(201, {"branch": new_branch, "base_sha": base_sha})
                except Exception as e:
                    logger.exception("create_branch failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.list_issues":
                repo_full = args.get("repo_full_name")
                state = args.get("state", "open")
                if not _validate_repo_full_name(repo_full):
                    return _base_response(400, error="repo_full_name required")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        issues = [{"number": i.number, "title": i.title, "state": i.state, "url": i.html_url} for i in repo.get_issues(state=state)]
                    else:
                        resp = client.get(f"{GITHUB_API_URL}/repos/{repo_full}/issues", params={"state": state})
                        resp.raise_for_status()
                        issues = [{"number": i.get("number"), "title": i.get("title"), "state": i.get("state"), "url": i.get("html_url")} for i in resp.json()]
                    return _base_response(200, issues)
                except Exception as e:
                    logger.exception("list_issues failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.create_issue":
                repo_full = args.get("repo_full_name")
                title = args.get("title")
                body = args.get("body", "")
                labels = args.get("labels", None)
                if not _validate_repo_full_name(repo_full) or not title:
                    return _base_response(400, error="repo_full_name and title required")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        issue = repo.create_issue(title=title, body=body, labels=labels)
                        return _base_response(201, {"number": issue.number, "url": issue.html_url})
                    else:
                        payload = {"title": title, "body": body}
                        if labels:
                            payload["labels"] = labels
                        resp = client.post(f"{GITHUB_API_URL}/repos/{repo_full}/issues", json=payload)
                        resp.raise_for_status()
                        j = resp.json()
                        return _base_response(201, {"number": j.get("number"), "url": j.get("html_url")})
                except Exception as e:
                    logger.exception("create_issue failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.create_pull_request":
                repo_full = args.get("repo_full_name")
                head = args.get("head")
                base = args.get("base")
                title = args.get("title")
                body = args.get("body", "")
                if not _validate_repo_full_name(repo_full) or not head or not base or not title:
                    return _base_response(400, error="repo_full_name, head, base, title required")
                try:
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        pr = repo.create_pull(title=title, body=body, head=head, base=base)
                        return _base_response(201, {"number": pr.number, "url": pr.html_url})
                    else:
                        payload = {"title": title, "head": head, "base": base, "body": body}
                        resp = client.post(f"{GITHUB_API_URL}/repos/{repo_full}/pulls", json=payload)
                        resp.raise_for_status()
                        j = resp.json()
                        return _base_response(201, {"number": j.get("number"), "url": j.get("html_url")})
                except Exception as e:
                    logger.exception("create_pull_request failed")
                    return _base_response(500, error=str(e))

            if tool_name == "github.get_commits":
                repo_full = args.get("repo_full_name")
                sha = args.get("sha", None)
                count = int(args.get("count", 10))
                if not _validate_repo_full_name(repo_full):
                    return _base_response(400, error="repo_full_name required")
                try:
                    commits_out = []
                    if HAVE_PYGITHUB and isinstance(client, Github):
                        repo = client.get_repo(repo_full)
                        iterator = repo.get_commits(sha=sha) if sha else repo.get_commits()
                        for i, c in enumerate(iterator):
                            commits_out.append({"sha": c.sha, "author": c.commit.author.name if c.commit and c.commit.author else None, "message": c.commit.message if c.commit else None, "date": c.commit.author.date.isoformat() if c.commit and c.commit.author else None})
                            if i + 1 >= count:
                                break
                    else:
                        params = {"sha": sha} if sha else {}
                        resp = client.get(f"{GITHUB_API_URL}/repos/{repo_full}/commits", params=params)
                        resp.raise_for_status()
                        for c in resp.json()[:count]:
                            commit = c.get("commit", {})
                            author = commit.get("author", {})
                            commits_out.append({"sha": c.get("sha"), "author": author.get("name"), "message": commit.get("message"), "date": author.get("date")})
                    return _base_response(200, commits_out)
                except Exception as e:
                    logger.exception("get_commits failed")
                    return _base_response(500, error=str(e))

            return _base_response(404, error=f"Unknown tool: {tool_name}")
        except Exception as e:
            logger.exception("Unhandled execute_tool error")
            return _base_response(500, error=str(e))


# Quick smoke tests when run directly (do not include secrets in source)
if __name__ == "__main__":
    s = GitHubMCPServer()
    # Example: run if environment contains GITHUB_PAT
    token = os.getenv(GITHUB_PAT_ENV)
    if token:
        print("Rate limit:", s.execute_tool("github.rate_limit", {"github_token": token}))
        print("List repos:", s.execute_tool("github.list_repos", {"limit": 5, "github_token": token}))
    else:
        print("No GITHUB_PAT found in environment. Export GITHUB_PAT to run smoke tests.")
