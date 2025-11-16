"""Okta tool: List users."""

from tools.base import BaseTool, ToolResult
from typing import Optional
import httpx
import os


class ListOktaUsersTool(BaseTool):
    """List users from Okta."""

    name = "list_okta_users"
    description = "List all users in Okta directory. Can filter by status or search term."
    is_write_operation = False
    parameters = {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of users to return (default: 20)",
                "default": 20,
            },
            "search": {
                "type": "string",
                "description": "Search term to filter users (searches email, firstName, lastName)",
            },
            "status": {
                "type": "string",
                "description": "Filter by user status (ACTIVE, DEPROVISIONED, etc.)",
                "enum": ["ACTIVE", "DEPROVISIONED", "STAGED", "SUSPENDED"],
            },
        },
    }

    async def execute(
        self,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ToolResult:
        """Execute the tool to list Okta users."""
        try:
            okta_domain = os.getenv("OKTA_DOMAIN")
            okta_token = os.getenv("OKTA_API_TOKEN")

            if not okta_domain or not okta_token:
                return ToolResult(
                    success=False,
                    error="Okta credentials not configured",
                )

            # Build URL
            url = f"https://{okta_domain}/api/v1/users"
            params = {"limit": limit}

            if search:
                params["search"] = search
            if status:
                params["filter"] = f'status eq "{status}"'

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"SSWS {okta_token}",
                        "Accept": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        error=f"Okta API error: {response.status_code} - {response.text}",
                    )

                users = response.json()

                # Format user data
                user_list = [
                    {
                        "id": user["id"],
                        "email": user["profile"].get("email"),
                        "firstName": user["profile"].get("firstName"),
                        "lastName": user["profile"].get("lastName"),
                        "status": user["status"],
                    }
                    for user in users
                ]

                return ToolResult(
                    success=True,
                    data=user_list,
                    metadata={"count": len(user_list)},
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list Okta users: {str(e)}",
            )
