"""Tool to get the current date and time."""

from datetime import datetime, timezone
from tools.base import BaseTool, ToolResult


class CurrentTimeTool(BaseTool):
    """
    Tool to get the current date and time.

    Returns the current UTC time and local time.
    """

    name = "get_current_time"
    description = "Get the current date and time in UTC and local timezone."
    parameters = {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "Optional timezone name (e.g., 'America/New_York', 'Europe/London'). Defaults to UTC and local.",
                "default": "UTC"
            }
        }
    }
    is_write_operation = False  # Read-only operation

    async def execute(self, timezone: str = "UTC") -> ToolResult:
        """
        Get the current time.

        Args:
            timezone: Optional timezone name

        Returns:
            ToolResult with current time information
        """
        try:
            utc_now = datetime.now(timezone.utc)
            local_now = datetime.now()

            time_info = {
                "utc_time": utc_now.isoformat(),
                "utc_timestamp": utc_now.timestamp(),
                "local_time": local_now.isoformat(),
                "local_timestamp": local_now.timestamp(),
                "timezone": timezone,
                "formatted": {
                    "utc": utc_now.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "local": local_now.strftime("%Y-%m-%d %H:%M:%S"),
                }
            }

            return ToolResult(
                success=True,
                data=time_info,
                metadata={"requested_timezone": timezone}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error getting current time: {str(e)}"
            )
