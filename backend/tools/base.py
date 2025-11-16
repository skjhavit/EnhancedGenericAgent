"""Base tool class for all agent tools."""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result from a tool execution."""

    success: bool
    data: Any = None
    error: str | None = None
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """
    Base class for all agent tools.

    Subclasses must implement:
    - name: Unique tool identifier
    - description: What the tool does
    - parameters: JSON Schema for parameters
    - execute: The actual tool logic
    """

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    is_write_operation: bool = False

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with provided parameters.

        Args:
            **kwargs: Tool parameters

        Returns:
            ToolResult with success status and data/error
        """
        pass

    def to_manifest(self) -> Dict[str, Any]:
        """
        Convert tool to manifest format for LLM.

        Returns:
            Dictionary with tool metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "requires_consent": self.is_write_operation,
        }

    def to_langchain_tool(self):
        """
        Convert to LangChain tool format.

        Returns:
            LangChain StructuredTool
        """
        from langchain.tools import StructuredTool

        return StructuredTool.from_function(
            name=self.name,
            description=self.description,
            func=self._sync_wrapper,
            coroutine=self._async_wrapper,
            args_schema=self._create_args_schema(),
        )

    async def _async_wrapper(self, **kwargs) -> str:
        """Async wrapper for LangChain compatibility."""
        result = await self.execute(**kwargs)
        if result.success:
            return str(result.data)
        else:
            return f"Error: {result.error}"

    def _sync_wrapper(self, **kwargs) -> str:
        """Sync wrapper for LangChain compatibility."""
        import asyncio
        return asyncio.run(self._async_wrapper(**kwargs))

    def _create_args_schema(self):
        """Create Pydantic schema from JSON Schema."""
        from pydantic import create_model, Field
        from typing import get_type_hints

        # Convert JSON Schema to Pydantic fields
        # This is a simplified version; you may need to enhance it
        fields = {}
        for prop_name, prop_schema in self.parameters.get("properties", {}).items():
            field_type = str  # Default to string
            if prop_schema.get("type") == "integer":
                field_type = int
            elif prop_schema.get("type") == "number":
                field_type = float
            elif prop_schema.get("type") == "boolean":
                field_type = bool

            fields[prop_name] = (
                field_type,
                Field(description=prop_schema.get("description", ""))
            )

        return create_model(f"{self.name}Schema", **fields)
