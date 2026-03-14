"""
System Info MCP Server
Returns real system metrics without requiring psutil.
Uses only standard library: os, platform, shutil, subprocess.
"""
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

try:
    from mcp_core import IMCPExternalServer, MCPTool
except ImportError:
    from .mcp_core import IMCPExternalServer, MCPTool

logger = logging.getLogger("system_info_mcp_server")
logger.setLevel(logging.INFO)

BACKEND_DIR = Path(__file__).parent.resolve()
SANDBOX_DIR = (BACKEND_DIR / "mcp_sandbox").resolve()

class SystemInfoMCPServer(IMCPExternalServer):
    """MCP Server providing system information using only standard library."""

    def __init__(self):
        super().__init__(name="system_info")
        logger.info("System Info MCP Server initialized")

    def list_tools(self) -> List[MCPTool]:
        return [
            MCPTool(
                name="system_info.get_system",
                description="Get OS, Python version, platform and machine info",
                parameters={"type": "object", "properties": {}}
            ),
            MCPTool(
                name="system_info.get_disk_usage",
                description="Get disk usage for the project sandbox directory",
                parameters={"type": "object", "properties": {}}
            ),
            MCPTool(
                name="system_info.list_sandbox_files",
                description="List all files in the mcp_sandbox with sizes and modification times",
                parameters={"type": "object", "properties": {}}
            ),
            MCPTool(
                name="system_info.get_environment",
                description="Get safe environment info: Python path, working directory, installed packages count",
                parameters={"type": "object", "properties": {}}
            )
        ]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "system_info.get_system":
                return {
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "os_release": platform.release(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": sys.version,
                    "python_executable": sys.executable,
                    "hostname": platform.node(),
                    "timestamp": datetime.now().isoformat(),
                    "code": 200
                }

            elif tool_name == "system_info.get_disk_usage":
                total, used, free = shutil.disk_usage(str(SANDBOX_DIR))
                sandbox_size = sum(
                    f.stat().st_size
                    for f in SANDBOX_DIR.rglob("*")
                    if f.is_file()
                ) if SANDBOX_DIR.exists() else 0

                return {
                    "sandbox_path": str(SANDBOX_DIR),
                    "sandbox_size_bytes": sandbox_size,
                    "sandbox_size_kb": round(sandbox_size / 1024, 2),
                    "disk_total_gb": round(total / (1024**3), 2),
                    "disk_used_gb": round(used / (1024**3), 2),
                    "disk_free_gb": round(free / (1024**3), 2),
                    "disk_used_percent": round((used / total) * 100, 1),
                    "code": 200
                }

            elif tool_name == "system_info.list_sandbox_files":
                if not SANDBOX_DIR.exists():
                    return {"files": [], "total": 0, "code": 200}

                files = []
                for f in sorted(SANDBOX_DIR.iterdir()):
                    if f.name.startswith("."):
                        continue
                    stat = f.stat()
                    files.append({
                        "name": f.name,
                        "type": "directory" if f.is_dir() else "file",
                        "size_bytes": stat.st_size if f.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    })

                return {
                    "sandbox_path": str(SANDBOX_DIR),
                    "files": files,
                    "total": len(files),
                    "code": 200
                }

            elif tool_name == "system_info.get_environment":
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "list", "--format=freeze"],
                        capture_output=True, text=True, timeout=5
                    )
                    package_count = len(result.stdout.strip().split("\n")) if result.returncode == 0 else 0
                except Exception:
                    package_count = 0

                return {
                    "python_executable": sys.executable,
                    "working_directory": os.getcwd(),
                    "project_backend": str(BACKEND_DIR),
                    "sandbox_directory": str(SANDBOX_DIR),
                    "installed_packages_count": package_count,
                    "platform": platform.platform(),
                    "code": 200
                }

            return {"error": f"Tool {tool_name} not found", "code": 404}

        except Exception as e:
            logger.exception(f"System info tool error: {e}")
            return {"error": str(e), "code": 500}
