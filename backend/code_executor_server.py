"""
Code Executor MCP Server
Safely runs Python code snippets in a subprocess with timeout.
Only uses standard library — no new pip installs needed.
"""
import logging
import subprocess
import sys
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

logger = logging.getLogger("code_executor_mcp_server")
logger.setLevel(logging.INFO)

BACKEND_DIR = Path(__file__).parent.resolve()
SANDBOX_DIR = (BACKEND_DIR / "mcp_sandbox").resolve()
MAX_OUTPUT_CHARS = 3000
EXECUTION_TIMEOUT = 10  # seconds

class CodeExecutorMCPServer(IMCPExternalServer):
    """MCP Server that safely executes Python code snippets."""

    def __init__(self):
        super().__init__(name="code_executor")
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Code Executor MCP Server initialized")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="code_executor.run_python",
                description="Execute a Python code snippet and return stdout/stderr output. Has a 10 second timeout. Can import standard library modules. Working directory is mcp_sandbox.",
                parameters={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Python code to execute"
                        }
                    },
                    "required": ["code"]
                }
            ),
            MCPTool(
                name="code_executor.run_python_file",
                description="Execute a Python file that exists in mcp_sandbox by filename",
                parameters={
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Filename in mcp_sandbox to run e.g. 'script.py'"
                        }
                    },
                    "required": ["filename"]
                }
            )
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "code_executor.run_python":
            code = args.get("code", "").strip()
            if not code:
                return {"error": "Code is required", "code": 400}
            return self._run_code(code)

        elif tool_name == "code_executor.run_python_file":
            filename = args.get("filename", "").strip()
            if not filename:
                return {"error": "Filename is required", "code": 400}
            # Sanitize - only allow simple filenames
            if "/" in filename or "\\" in filename or ".." in filename:
                return {"error": "Invalid filename - no paths allowed", "code": 400}
            filepath = SANDBOX_DIR / filename
            if not filepath.exists():
                return {"error": f"File '{filename}' not found in sandbox", "code": 404}
            try:
                code = filepath.read_text(encoding="utf-8")
                return self._run_code(code, working_dir=str(SANDBOX_DIR))
            except Exception as e:
                return {"error": str(e), "code": 500}

        return {"error": f"Tool {tool_name} not found", "code": 404}

    def _run_code(self, code: str, working_dir: str = None) -> Dict[str, Any]:
        """Run Python code in subprocess with timeout."""
        if working_dir is None:
            working_dir = str(SANDBOX_DIR)

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False,
                dir=str(SANDBOX_DIR), prefix=".tmp_exec_",
                encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT,
                cwd=working_dir
            )

            stdout = result.stdout[:MAX_OUTPUT_CHARS] if result.stdout else ""
            stderr = result.stderr[:MAX_OUTPUT_CHARS] if result.stderr else ""

            if len(result.stdout) > MAX_OUTPUT_CHARS:
                stdout += f"\n...[truncated, {len(result.stdout)} chars total]"
            if len(result.stderr) > MAX_OUTPUT_CHARS:
                stderr += f"\n...[truncated]"

            return {
                "stdout": stdout,
                "stderr": stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
                "code": 200
            }

        except subprocess.TimeoutExpired:
            return {
                "error": f"Code execution timed out after {EXECUTION_TIMEOUT} seconds",
                "code": 408
            }
        except Exception as e:
            logger.exception(f"Code execution error: {e}")
            return {"error": str(e), "code": 500}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
