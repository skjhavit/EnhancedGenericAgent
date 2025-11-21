"""
Get App Registration Tool
Retrieves application registration details from Azure Active Directory (Entra ID).
"""
from tools.azure.base import AzureReadTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class GetAppRegistrationTool(AzureReadTool):
    """
    Retrieve application registration details from Azure Active Directory.

    This tool is used for:
    - Verification after app registration creation/updates
    - Investigation when troubleshooting authentication issues
    - Reviewing app configuration and permissions

    No consent required (read operation).
    """

    name = "get_app_registration"
    description = (
        "Retrieve detailed information about an application registration from Azure AD. "
        "Use for verification after creating/updating apps or for troubleshooting. "
        "Accepts either app object ID or application (client) ID."
    )
    parameters = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": (
                    "Application identifier: either object ID (GUID) or "
                    "application (client) ID (GUID)"
                )
            }
        },
        "required": ["id"]
    }

    is_write_operation = False

    async def execute(self, id: str, **kwargs) -> ToolResult:
        """
        Execute app registration retrieval.

        Args:
            id: Application object ID or application (client) ID

        Returns:
            ToolResult with app registration details if found
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            logger.info(f"Retrieving app registration: {id}")

            # Try to get by object ID first
            try:
                app = await client.applications.by_application_id(id).get()
            except:
                # If that fails, try filtering by appId (application/client ID)
                filter_query = f"appId eq '{id}'"
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
                        error=f"Application registration not found: {id}",
                        metadata={"queried_id": id}
                    )

            logger.info(
                f"App registration retrieved: {app.display_name} "
                f"(ID: {app.id}, AppID: {app.app_id})"
            )

            # Extract redirect URIs
            web_redirect_uris = []
            spa_redirect_uris = []

            if app.web and app.web.redirect_uris:
                web_redirect_uris = list(app.web.redirect_uris)

            if app.spa and app.spa.redirect_uris:
                spa_redirect_uris = list(app.spa.redirect_uris)

            # Return comprehensive app data
            result_data = {
                "id": app.id,  # Object ID
                "app_id": app.app_id,  # Application (client) ID
                "display_name": app.display_name,
                "sign_in_audience": app.sign_in_audience,
                "web_redirect_uris": web_redirect_uris,
                "spa_redirect_uris": spa_redirect_uris,
                "publisher_domain": app.publisher_domain,
                "created_date_time": str(app.created_date_time) if app.created_date_time else None,
                "identifier_uris": list(app.identifier_uris) if app.identifier_uris else []
            }

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "resource_type": "application",
                    "queried_id": id,
                    "note": f"Use Application ID {app.app_id} for authentication configuration"
                }
            )

        except Exception as e:
            logger.error(f"Failed to retrieve app registration {id}: {str(e)}")
            return await self._handle_azure_error(e)
