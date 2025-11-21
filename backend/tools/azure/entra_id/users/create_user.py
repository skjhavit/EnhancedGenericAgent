"""
Create User Tool
Creates a new user in Azure Active Directory (Entra ID).
"""
from typing import Optional
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile
import logging

logger = logging.getLogger(__name__)


class CreateUserTool(AzureWriteTool):
    """
    Create a new user account in Azure Active Directory.

    This tool provisions a new user with specified attributes and a temporary password.

    Security Features:
    - Automatically sets forceChangePasswordNextSignIn=True for security
    - Requires consent approval (is_write_operation=True)
    - Validates required parameters
    - Supports verification via get_user tool
    """

    name = "create_user"
    description = (
        "Create a new user account in Azure Active Directory (Entra ID). "
        "User will be required to change password on first login. "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "user_principal_name": {
                "type": "string",
                "description": "User's email address / UPN (e.g., john.doe@company.com)"
            },
            "display_name": {
                "type": "string",
                "description": "Full name displayed in Azure AD (e.g., 'John Doe')"
            },
            "mail_nickname": {
                "type": "string",
                "description": "Email alias / mail nickname (e.g., 'john.doe')"
            },
            "password": {
                "type": "string",
                "description": "Temporary password (min 8 chars, complexity required)"
            },
            "account_enabled": {
                "type": "boolean",
                "description": "Enable account immediately (default: true)",
                "default": True
            },
            "job_title": {
                "type": "string",
                "description": "Optional: User's job title"
            },
            "department": {
                "type": "string",
                "description": "Optional: User's department"
            },
            "office_location": {
                "type": "string",
                "description": "Optional: Office location"
            }
        },
        "required": ["user_principal_name", "display_name", "mail_nickname", "password"]
    }

    is_write_operation = True
    verification_tool_name = "get_user"

    async def execute(
        self,
        user_principal_name: str,
        display_name: str,
        mail_nickname: str,
        password: str,
        account_enabled: bool = True,
        job_title: Optional[str] = None,
        department: Optional[str] = None,
        office_location: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute user creation.

        Args:
            user_principal_name: User's UPN (email)
            display_name: Display name
            mail_nickname: Email alias
            password: Temporary password
            account_enabled: Enable account (default: True)
            job_title: Optional job title
            department: Optional department
            office_location: Optional office location

        Returns:
            ToolResult with user details if successful
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # Create password profile
            password_profile = PasswordProfile(
                password=password,
                force_change_password_next_sign_in=True  # Security best practice
            )

            # Build user object
            user = User()
            user.account_enabled = account_enabled
            user.display_name = display_name
            user.mail_nickname = mail_nickname
            user.user_principal_name = user_principal_name
            user.password_profile = password_profile

            # Add optional attributes
            if job_title:
                user.job_title = job_title
            if department:
                user.department = department
            if office_location:
                user.office_location = office_location

            # Create user via Graph API
            logger.info(f"Creating user: {user_principal_name}")
            created_user = await client.users.post(user)

            logger.info(
                f"User created successfully: {created_user.user_principal_name} "
                f"(ID: {created_user.id})"
            )

            result_data = {
                "id": created_user.id,
                "user_principal_name": created_user.user_principal_name,
                "display_name": created_user.display_name,
                "account_enabled": created_user.account_enabled,
                "job_title": created_user.job_title,
                "department": created_user.department,
                "office_location": created_user.office_location
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "created",
                    "resource_type": "user",
                    "verification_hint": verification_hint,
                    "security_note": "User must change password on first login"
                }
            )

        except Exception as e:
            logger.error(f"Failed to create user {user_principal_name}: {str(e)}")
            return await self._handle_azure_error(e)
