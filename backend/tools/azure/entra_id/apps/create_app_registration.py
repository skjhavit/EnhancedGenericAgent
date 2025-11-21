"""
Create App Registration Tool
Creates a new application registration in Azure Active Directory (Entra ID).
"""
from typing import Optional, List
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.application import Application
import logging

logger = logging.getLogger(__name__)


class CreateAppRegistrationTool(AzureWriteTool):
    """
    Create a new application registration in Azure Active Directory.

    App registrations are used for:
    - OAuth 2.0 authentication flows
    - Service-to-service authentication
    - API access with specific permissions
    - Single sign-on (SSO) applications

    Security Features:
    - Requires consent approval (is_write_operation=True)
    - Supports single-tenant (most secure) or multi-tenant apps
    - No client secrets created automatically (use create_client_secret separately)
    - Verification via get_app_registration tool
    """

    name = "create_app_registration"
    description = (
        "Create a new application registration in Azure AD for OAuth/API authentication. "
        "Use for creating apps that need to authenticate users or access Microsoft Graph API. "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "display_name": {
                "type": "string",
                "description": "Application display name (e.g., 'Finance API Production')"
            },
            "sign_in_audience": {
                "type": "string",
                "enum": [
                    "AzureADMyOrg",
                    "AzureADMultipleOrgs",
                    "AzureADandPersonalMicrosoftAccount"
                ],
                "description": (
                    "Who can use this application:\n"
                    "- AzureADMyOrg: Single tenant (most secure, default)\n"
                    "- AzureADMultipleOrgs: Multi-tenant (any Azure AD)\n"
                    "- AzureADandPersonalMicrosoftAccount: Public (includes personal MS accounts)"
                ),
                "default": "AzureADMyOrg"
            },
            "web_redirect_uris": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: Web redirect URIs for OAuth (e.g., ['https://app.com/callback'])"
            },
            "spa_redirect_uris": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional: SPA redirect URIs for public clients (e.g., ['http://localhost:3000'])"
            }
        },
        "required": ["display_name"]
    }

    is_write_operation = True
    verification_tool_name = "get_app_registration"

    async def execute(
        self,
        display_name: str,
        sign_in_audience: str = "AzureADMyOrg",
        web_redirect_uris: Optional[List[str]] = None,
        spa_redirect_uris: Optional[List[str]] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute app registration creation.

        Args:
            display_name: Application display name
            sign_in_audience: Who can use this app (default: single tenant)
            web_redirect_uris: Optional web redirect URIs
            spa_redirect_uris: Optional SPA redirect URIs

        Returns:
            ToolResult with app registration details
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # Build application object
            app = Application()
            app.display_name = display_name
            app.sign_in_audience = sign_in_audience

            # Configure redirect URIs if provided
            if web_redirect_uris or spa_redirect_uris:
                from msgraph.generated.models.web_application import WebApplication
                from msgraph.generated.models.spa_application import SpaApplication

                if web_redirect_uris:
                    web = WebApplication()
                    web.redirect_uris = web_redirect_uris
                    app.web = web

                if spa_redirect_uris:
                    spa = SpaApplication()
                    spa.redirect_uris = spa_redirect_uris
                    app.spa = spa

            # Create app registration via Graph API
            logger.info(
                f"Creating app registration: {display_name} "
                f"(audience: {sign_in_audience})"
            )

            created_app = await client.applications.post(app)

            logger.info(
                f"App registration created: {created_app.display_name} "
                f"(ID: {created_app.id}, AppID: {created_app.app_id})"
            )

            result_data = {
                "id": created_app.id,  # Object ID
                "app_id": created_app.app_id,  # Application (client) ID
                "display_name": created_app.display_name,
                "sign_in_audience": created_app.sign_in_audience,
                "web_redirect_uris": web_redirect_uris or [],
                "spa_redirect_uris": spa_redirect_uris or [],
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "created",
                    "resource_type": "application",
                    "verification_hint": verification_hint,
                    "security_note": (
                        "App created successfully. "
                        "To enable authentication:\n"
                        "1. Use create_client_secret to generate credentials (or configure certificate)\n"
                        "2. Configure API permissions in Azure Portal if needed\n"
                        "3. Grant admin consent for permissions"
                    ),
                    "important": (
                        f"Application (client) ID: {created_app.app_id} "
                        f"(use this for authentication configuration)"
                    )
                }
            )

        except Exception as e:
            logger.error(f"Failed to create app registration {display_name}: {str(e)}")
            return await self._handle_azure_error(e)
