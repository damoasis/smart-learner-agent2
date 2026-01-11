"""Simplified ToolExecutor compatible with existing ReAct agents.

This avoids depending on langgraph.prebuilt.ToolExecutor, which is not
available in the current langgraph version.

The executor takes a list of LangChain tools (decorated with @tool) and
executes them based on the tool_call dict produced by the LLM.
"""
from __future__ import annotations

from typing import Any, Dict, List


class ToolExecutor:
    """Minimal ToolExecutor implementation.

    Expected tool_call shape (as used in existing agents):
    {
        "id": str,
        "name": str,
        "args": dict
    }

    Tools are LangChain tools created by @tool decorator, so they support
    .invoke(**kwargs) or .invoke(args) with a dict.
    """

    def __init__(self, tools: List[Any]) -> None:
        # Tools are LangChain `BaseTool` instances with a `.name` attribute.
        self._tools: Dict[str, Any] = {}
        for tool in tools:
            name = getattr(tool, "name", None)
            if not name:
                # Fallback: use __name__ if available
                name = getattr(tool, "__name__", None)
            if not name:
                continue
            self._tools[name] = tool

    def invoke(self, tool_call: Dict[str, Any]) -> Any:
        """Execute a single tool call.

        Args:
            tool_call: Dict with `name` and `args` keys.
        """
        name = tool_call.get("name")
        args = tool_call.get("args") or {}

        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Unknown tool: {name}")

        # LangChain tools generally expose `.invoke` for structured input.
        if hasattr(tool, "invoke"):
            # If the tool expects keyword arguments, passing the dict directly
            # is acceptable; LangChain will handle mapping.
            return tool.invoke(args)

        # Fallback: try calling as a normal callable.
        if isinstance(args, dict):
            return tool(**args)
        return tool(args)
