"""
Add Redirect URI Tool
Adds a redirect URI to an existing application registration in Azure AD.
"""
from typing import Literal
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.application import Application
from msgraph.generated.models.web_application import WebApplication
from msgraph.generated.models.spa_application import SpaApplication
import logging

logger = logging.getLogger(__name__)


class AddRedirectUriTool(AzureWriteTool):
    """
    Add a redirect URI to an existing application registration.

    Redirect URIs are required for OAuth 2.0 authentication flows.

    Types:
    - Web: For server-side apps (confidential clients)
    - SPA: For single-page applications (public clients)

    Security Features:
    - Requires consent approval (is_write_operation=True)
    - Validates URI format
    - Supports verification via get_app_registration tool
    """

    name = "add_redirect_uri"
    description = (
        "Add a redirect URI to an application registration for OAuth authentication. "
        "Choose 'web' for server-side apps or 'spa' for single-page applications. "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "app_id": {
                "type": "string",
                "description": "Application object ID or application (client) ID"
            },
            "redirect_uri": {
                "type": "string",
                "description": "Redirect URI to add (e.g., 'https://app.company.com/callback')"
            },
            "platform": {
                "type": "string",
                "enum": ["web", "spa"],
                "description": (
                    "Platform type:\n"
                    "- web: Server-side app (confidential client)\n"
                    "- spa: Single-page app (public client, PKCE required)"
                ),
                "default": "web"
            }
        },
        "required": ["app_id", "redirect_uri"]
    }

    is_write_operation = True
    verification_tool_name = "get_app_registration"

    async def execute(
        self,
        app_id: str,
        redirect_uri: str,
        platform: Literal["web", "spa"] = "web",
        **kwargs
    ) -> ToolResult:
        """
        Execute redirect URI addition.

        Args:
            app_id: Application object ID or client ID
            redirect_uri: Redirect URI to add
            platform: Platform type (web or spa)

        Returns:
            ToolResult with updated app details
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # First, retrieve the existing application
            logger.info(f"Retrieving app registration: {app_id}")

            try:
                app = await client.applications.by_application_id(app_id).get()
            except:
                # Try filtering by appId
                filter_query = f"appId eq '{app_id}'"
                apps = await client.applications.get(
                    request_configuration=lambda config: setattr(
                        config.query_parameters, 'filter', filter_query
                    )
                )

                if apps and apps.value and len(apps.value) > 0:
                    app = apps.value[0]
                else:
                    return ToolResult(
                        success=False,
                        error=f"Application not found: {app_id}",
                        metadata={"app_id": app_id}
                    )

            # Get existing redirect URIs
            existing_web_uris = list(app.web.redirect_uris) if app.web and app.web.redirect_uris else []
            existing_spa_uris = list(app.spa.redirect_uris) if app.spa and app.spa.redirect_uris else []

            # Check if URI already exists
            if platform == "web" and redirect_uri in existing_web_uris:
                return ToolResult(
                    success=True,
                    data={
                        "id": app.id,
                        "app_id": app.app_id,
                        "display_name": app.display_name,
                        "redirect_uri": redirect_uri,
                        "platform": platform,
                        "already_exists": True
                    },
                    metadata={
                        "action": "no_change",
                        "note": f"Redirect URI already exists in {platform} platform"
                    }
                )

            if platform == "spa" and redirect_uri in existing_spa_uris:
                return ToolResult(
                    success=True,
                    data={
                        "id": app.id,
                        "app_id": app.app_id,
                        "display_name": app.display_name,
                        "redirect_uri": redirect_uri,
                        "platform": platform,
                        "already_exists": True
                    },
                    metadata={
                        "action": "no_change",
                        "note": f"Redirect URI already exists in {platform} platform"
                    }
                )

            # Add the new redirect URI
            update_app = Application()

            if platform == "web":
                existing_web_uris.append(redirect_uri)
                web = WebApplication()
                web.redirect_uris = existing_web_uris
                update_app.web = web
            else:  # spa
                existing_spa_uris.append(redirect_uri)
                spa = SpaApplication()
                spa.redirect_uris = existing_spa_uris
                update_app.spa = spa

            logger.info(
                f"Adding {platform} redirect URI to app {app.display_name}: {redirect_uri}"
            )

            # Update the application
            await client.applications.by_application_id(app.id).patch(update_app)

            logger.info(f"Redirect URI added successfully to {app.display_name}")

            result_data = {
                "id": app.id,
                "app_id": app.app_id,
                "display_name": app.display_name,
                "redirect_uri": redirect_uri,
                "platform": platform,
                "total_web_uris": len(existing_web_uris),
                "total_spa_uris": len(existing_spa_uris)
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "redirect_uri_added",
                    "resource_type": "application",
                    "verification_hint": verification_hint,
                    "note": (
                        f"Redirect URI added to {platform} platform. "
                        f"You can now use this URI in your OAuth flow."
                    )
                }
            )

        except Exception as e:
            logger.error(f"Failed to add redirect URI to app {app_id}: {str(e)}")
            return await self._handle_azure_error(e)
