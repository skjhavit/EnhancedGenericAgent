"""Tool registry for managing available tools."""

from typing import Dict, List, Any, Optional
from tools.base import BaseTool


class ToolRegistry:
    """
    Global registry for all available tools.

    Tools must be registered before they can be used by agents.
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool from the registry.

        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_manifest(self, tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get tool manifests for specified tools or all tools.

        Args:
            tool_names: Optional list of tool names to include

        Returns:
            List of tool manifests
        """
        if tool_names is None:
            # Return all tools
            return [tool.to_manifest() for tool in self._tools.values()]
        else:
            # Return only specified tools
            manifests = []
            for tool_name in tool_names:
                tool = self.get_tool(tool_name)
                if tool:
                    manifests.append(tool.to_manifest())
            return manifests

    def get_write_operation_tools(self) -> List[str]:
        """
        Get list of tools that are write operations.

        Returns:
            List of tool names that require consent
        """
        return [
            name
            for name, tool in self._tools.items()
            if tool.is_write_operation
        ]


# Global tool registry instance
tool_registry = ToolRegistry()
