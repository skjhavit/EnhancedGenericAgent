"""
Get User Tool
Retrieves user details from Azure Active Directory (Entra ID).
"""
from tools.azure.base import AzureReadTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class GetUserTool(AzureReadTool):
    """
    Retrieve user details from Azure Active Directory.

    This tool is used for:
    - Verification after user creation/updates
    - Investigation when troubleshooting access issues
    - General user information lookup

    No consent required (read operation).
    """

    name = "get_user"
    description = (
        "Retrieve detailed information about a user from Azure Active Directory. "
        "Use for verification after creating/updating users or for troubleshooting. "
        "Accepts either user ID (object ID) or UPN (email)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": (
                    "User identifier: either object ID (GUID) or "
                    "User Principal Name (email, e.g., john.doe@company.com)"
                )
            }
        },
        "required": ["id"]
    }

    is_write_operation = False

    async def execute(self, id: str, **kwargs) -> ToolResult:
        """
        Execute user retrieval.

        Args:
            id: User object ID or User Principal Name (UPN)

        Returns:
            ToolResult with user details if found
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            logger.info(f"Retrieving user: {id}")

            # Get user by ID or UPN
            user = await client.users.by_user_id(id).get()

            if not user:
                return ToolResult(
                    success=False,
                    error=f"User not found: {id}",
                    metadata={"queried_id": id}
                )

            logger.info(f"User retrieved: {user.user_principal_name} (ID: {user.id})")

            # Return comprehensive user data
            result_data = {
                "id": user.id,
                "user_principal_name": user.user_principal_name,
                "display_name": user.display_name,
                "mail": user.mail,
                "mail_nickname": user.mail_nickname,
                "account_enabled": user.account_enabled,
                "job_title": user.job_title,
                "department": user.department,
                "office_location": user.office_location,
                "mobile_phone": user.mobile_phone,
                "business_phones": user.business_phones,
                "city": user.city,
                "country": user.country,
                "state": user.state,
                "postal_code": user.postal_code,
                "street_address": user.street_address,
                "usage_location": user.usage_location,
                "user_type": user.user_type,
                "created_date_time": str(user.created_date_time) if user.created_date_time else None
            }

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "resource_type": "user",
                    "queried_id": id
                }
            )

        except Exception as e:
            logger.error(f"Failed to retrieve user {id}: {str(e)}")
            return await self._handle_azure_error(e)
