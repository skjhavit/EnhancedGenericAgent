"""
Create Client Secret Tool
Creates a client secret for an application registration in Azure AD.
"""
from typing import Literal
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.password_credential import PasswordCredential
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CreateClientSecretTool(AzureWriteTool):
    """
    Create a client secret for an application registration.

    ⚠️  SECURITY WARNING ⚠️
    - Client secrets are sensitive credentials
    - Secret value is shown ONLY once (during creation)
    - Prefer certificate-based authentication when possible
    - Use shortest acceptable expiration period
    - Rotate secrets regularly

    Use Cases:
    - Service-to-service authentication
    - Daemon/background applications
    - CI/CD pipelines

    Security Features:
    - Requires consent approval (is_write_operation=True)
    - Maximum 6-month expiration enforced (security best practice)
    - Supports verification via get_app_registration tool
    """

    name = "create_client_secret"
    description = (
        "⚠️ SENSITIVE: Create a client secret for app authentication. "
        "Secret value is shown ONLY ONCE. Prefer certificate auth when possible. "
        "Maximum 6-month expiration enforced. This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "app_id": {
                "type": "string",
                "description": "Application object ID or application (client) ID"
            },
            "description": {
                "type": "string",
                "description": (
                    "Secret description (e.g., 'Production API Secret - Expires 2024-06'). "
                    "Use descriptive names for tracking/rotation."
                )
            },
            "expiration_months": {
                "type": "integer",
                "enum": [1, 3, 6],
                "description": (
                    "Expiration period in months (max 6 months for security). "
                    "Options: 1, 3, or 6 months. Default: 6 months."
                ),
                "default": 6
            }
        },
        "required": ["app_id", "description"]
    }

    is_write_operation = True
    verification_tool_name = "get_app_registration"

    async def execute(
        self,
        app_id: str,
        description: str,
        expiration_months: Literal[1, 3, 6] = 6,
        **kwargs
    ) -> ToolResult:
        """
        Execute client secret creation.

        Args:
            app_id: Application object ID or client ID
            description: Secret description
            expiration_months: Expiration in months (1, 3, or 6)

        Returns:
            ToolResult with secret value (⚠️ shown only once!)
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

            # Calculate expiration date
            end_date_time = datetime.utcnow() + timedelta(days=expiration_months * 30)

            # Create password credential (client secret)
            password_credential = PasswordCredential()
            password_credential.display_name = description
            password_credential.end_date_time = end_date_time

            logger.warning(
                f"⚠️  Creating client secret for app {app.display_name} "
                f"(expires: {end_date_time.strftime('%Y-%m-%d')})"
            )

            # Add password credential to the application
            from msgraph.generated.applications.item.add_password.add_password_post_request_body import (
                AddPasswordPostRequestBody
            )

            request_body = AddPasswordPostRequestBody()
            request_body.password_credential = password_credential

            result = await client.applications.by_application_id(app.id).add_password.post(
                request_body
            )

            if not result or not result.secret_text:
                return ToolResult(
                    success=False,
                    error="Failed to create client secret (no secret value returned)",
                    metadata={"app_id": app_id}
                )

            logger.warning(
                f"⚠️  Client secret created for {app.display_name}. "
                f"Secret ID: {result.key_id}"
            )

            result_data = {
                "id": app.id,
                "app_id": app.app_id,
                "display_name": app.display_name,
                "secret_id": result.key_id,
                "secret_value": result.secret_text,  # ⚠️ SHOWN ONLY ONCE!
                "description": description,
                "created_date_time": str(datetime.utcnow()),
                "expiration_date_time": end_date_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
                "expiration_months": expiration_months
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "client_secret_created",
                    "resource_type": "application",
                    "verification_hint": verification_hint,
                    "security_warning": (
                        "⚠️  CRITICAL: Store this secret securely NOW. "
                        "It will NOT be shown again.\n\n"
                        "Best Practices:\n"
                        "- Store in Azure Key Vault or secure secrets manager\n"
                        "- Never commit to source control\n"
                        "- Set reminder to rotate before expiration\n"
                        "- Use certificate auth instead when possible"
                    ),
                    "rotation_reminder": (
                        f"Secret expires: {end_date_time.strftime('%Y-%m-%d')}. "
                        f"Set reminder to rotate before this date."
                    )
                }
            )

        except Exception as e:
            logger.error(f"Failed to create client secret for app {app_id}: {str(e)}")
            return await self._handle_azure_error(e)
