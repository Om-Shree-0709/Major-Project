# backend/mcp_core.py
from __future__ import annotations
import logging
import inspect
import asyncio
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

# Optional dependency for robust JSON Schema validation
try:
    import jsonschema  # type: ignore
    HAVE_JSONSCHEMA = True
except Exception:
    HAVE_JSONSCHEMA = False

logger = logging.getLogger("mcp_core")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)


class MCPTool(BaseModel):
    """
    Description of a single tool that an MCP server exposes.
    `parameters` should follow JSON Schema (object schema) describing the tool's input.
    """
    name: str = Field(..., description="Unique tool name, e.g. 'filesystem.read_file'")
    description: str = Field(..., description="Human/LLM-friendly description of the tool")
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []},
        description="JSON Schema (object) for tool parameters (OpenAPI/JSON Schema format)",
    )


class ToolExecutionError(Exception):
    """Raised when a tool execution fails in a predictable way."""
    def __init__(self, message: str, code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.code = code
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        out = {"error": str(self)}
        if self.code is not None:
            out["code"] = self.code
        if self.details is not None:
            out["details"] = self.details
        return out


class IMCPExternalServer(ABC):
    """
    Abstract base class for MCP external servers (Filesystem, Browser, GitHub, etc).
    - `list_tools()` should return a list of MCPTool instances (discovery).
    - `execute_tool(tool_name, args)` may be either a synchronous function or an async coroutine.
      Use `await run_tool(tool_name, args)` to invoke in a uniform async manner.
    """

    def __init__(self, name: str):
        self.name = name
        logger.info("Initialized MCP server: %s", self.name)

    @abstractmethod
    def list_tools(self) -> List[MCPTool]:
        """Return tools (MCPTool) that this server exposes for discovery."""
        raise NotImplementedError

    # NOTE: implementers MAY define execute_tool as `def execute_tool(...)` (sync)
    # or `async def execute_tool(...)` (async). The run_tool wrapper handles both.
    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional synchronous implementation of executing a tool.
        Override in subclasses if you prefer a synchronous execution model.
        """
        raise NotImplementedError("execute_tool not implemented (sync)")

    async def async_execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optional asynchronous implementation.
        Subclasses can implement this instead of `execute_tool`.
        The run_tool wrapper will call whichever is implemented.
        """
        raise NotImplementedError("async_execute_tool not implemented (async)")

    async def run_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified async wrapper to execute a tool. This will:
        1. Validate that the tool exists.
        2. Validate args against the tool's schema (best-effort).
        3. Call either `async_execute_tool` if implemented, or synchronous `execute_tool` in a thread.
        4. Normalize exceptions into ToolExecutionError or structured dict.
        """
        try:
            tool = self.tool_by_name(tool_name)
            if not tool:
                raise ToolExecutionError(f"Tool '{tool_name}' not found on server '{self.name}'", code=404)

            # Validate args (best-effort)
            try:
                self.validate_args(tool, args or {})
            except ToolExecutionError:
                raise
            except Exception as e:
                # validation failure treated as bad request
                raise ToolExecutionError(f"Invalid arguments for tool '{tool_name}': {e}", code=400)

            # prefer explicit async implementation if provided
            impl_async = getattr(self, "async_execute_tool", None)
            impl_sync = getattr(self, "execute_tool", None)

            # If subclass implemented async_execute_tool (and not the base), call it
            if impl_async is not None and impl_async is not IMCPExternalServer.async_execute_tool:
                if inspect.iscoroutinefunction(impl_async):
                    return await impl_async(tool_name, args)
                # fallback if user provided non-async function under that name
                result = impl_async(tool_name, args)
                if inspect.isawaitable(result):
                    return await result
                return result

            # If subclass implemented a synchronous execute_tool, run it in threadpool
            if impl_sync is not None and impl_sync is not IMCPExternalServer.execute_tool:
                if inspect.iscoroutinefunction(impl_sync):
                    # unexpected but handle coroutine
                    return await impl_sync(tool_name, args)
                # run blocking sync function in executor
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: impl_sync(tool_name, args))

            raise ToolExecutionError("No tool execution method implemented in server", code=501)
        except ToolExecutionError:
            raise
        except Exception as e:
            logger.exception("Unhandled exception running tool %s on server %s", tool_name, self.name)
            # wrap unknown errors
            raise ToolExecutionError(str(e), code=500)

    def tool_by_name(self, tool_name: str) -> Optional[MCPTool]:
        """Find an MCPTool by name (case-sensitive)."""
        for t in self.list_tools() or []:
            if t.name == tool_name:
                return t
        return None

    def validate_args(self, tool: MCPTool, args: Dict[str, Any]) -> None:
        """
        Validate `args` against tool.parameters (JSON Schema) if jsonschema is installed.
        If jsonschema is not available, perform a lightweight check of required properties.
        Raises ToolExecutionError with code 400 on validation failure.
        """
        if not isinstance(args, dict):
            raise ToolExecutionError("Tool arguments must be an object/dict", code=400)

        schema = tool.parameters or {}
        # schema is expected to be an object schema
        if HAVE_JSONSCHEMA and isinstance(schema, dict):
            try:
                jsonschema.validate(instance=args, schema=schema)
            except Exception as ve:  # jsonschema.ValidationError or similar
                raise ToolExecutionError(f"Argument validation failed: {ve}", code=400, details=getattr(ve, "message", str(ve)))
        else:
            # Lightweight fallback: check required fields in schema if present
            required = None
            try:
                required = schema.get("required", None) if isinstance(schema, dict) else None
            except Exception:
                required = None
            if required:
                missing = [r for r in required if r not in args]
                if missing:
                    raise ToolExecutionError(f"Missing required parameters: {missing}", code=400)

    # Utility for subclasses to return consistent error dicts
    @staticmethod
    def make_error(message: str, code: int = 400, details: Optional[Any] = None) -> Dict[str, Any]:
        err = {"error": message, "code": code}
        if details is not None:
            err["details"] = details
        return err
