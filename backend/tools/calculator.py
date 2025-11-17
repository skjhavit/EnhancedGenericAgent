"""Calculator tool for basic mathematical operations."""

from tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """
    Tool for performing basic mathematical calculations.

    This is a simple example tool that demonstrates tool execution.
    """

    name = "calculator"
    description = "Perform basic mathematical calculations. Supports addition, subtraction, multiplication, division, and exponentiation."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5', '2 ** 3')"
            }
        },
        "required": ["expression"]
    }
    is_write_operation = False  # Read-only operation

    async def execute(self, expression: str) -> ToolResult:
        """
        Execute the calculator.

        Args:
            expression: Mathematical expression to evaluate

        Returns:
            ToolResult with the calculation result
        """
        try:
            # Safety: Only allow basic math operations
            allowed_chars = set("0123456789+-*/().** ")
            if not all(c in allowed_chars for c in expression):
                return ToolResult(
                    success=False,
                    error="Invalid characters in expression. Only numbers and +, -, *, /, **, (, ) are allowed."
                )

            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, {})

            return ToolResult(
                success=True,
                data=result,
                metadata={"expression": expression}
            )

        except ZeroDivisionError:
            return ToolResult(
                success=False,
                error="Division by zero"
            )
        except SyntaxError:
            return ToolResult(
                success=False,
                error="Invalid mathematical expression"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}"
            )
