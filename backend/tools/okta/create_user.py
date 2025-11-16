"""Okta tool: Create user."""

from tools.base import BaseTool, ToolResult
from typing import Optional
import httpx
import os


class CreateOktaUserTool(BaseTool):
    """Create a new user in Okta."""

    name = "create_okta_user"
    description = "Create a new user in Okta directory. This is a write operation that requires user approval."
    is_write_operation = True  # Requires consent!
    parameters = {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "User's email address (will be used as login)",
            },
            "firstName": {
                "type": "string",
                "description": "User's first name",
            },
            "lastName": {
                "type": "string",
                "description": "User's last name",
            },
            "activate": {
                "type": "boolean",
                "description": "Whether to activate the user immediately (default: true)",
                "default": True,
            },
        },
        "required": ["email", "firstName", "lastName"],
    }

    async def execute(
        self,
        email: str,
        firstName: str,
        lastName: str,
        activate: bool = True,
    ) -> ToolResult:
        """Execute the tool to create an Okta user."""
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
            params = {"activate": str(activate).lower()}

            # Build user payload
            payload = {
                "profile": {
                    "firstName": firstName,
                    "lastName": lastName,
                    "email": email,
                    "login": email,
                },
            }

            # Make API request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params=params,
                    json=payload,
                    headers={
                        "Authorization": f"SSWS {okta_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    timeout=30.0,
                )

                if response.status_code not in [200, 201]:
                    return ToolResult(
                        success=False,
                        error=f"Okta API error: {response.status_code} - {response.text}",
                    )

                user = response.json()

                return ToolResult(
                    success=True,
                    data={
                        "id": user["id"],
                        "email": user["profile"]["email"],
                        "firstName": user["profile"]["firstName"],
                        "lastName": user["profile"]["lastName"],
                        "status": user["status"],
                        "created": user["created"],
                    },
                    metadata={"activated": activate},
                )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to create Okta user: {str(e)}",
            )
