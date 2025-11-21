"""
Reset Password Tool
Resets a user's password in Azure Active Directory (Entra ID).
"""
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile
import logging
import secrets
import string

logger = logging.getLogger(__name__)


class ResetPasswordTool(AzureWriteTool):
    """
    Reset a user's password in Azure Active Directory.

    Security Features:
    - Generates secure temporary password if not provided
    - Automatically sets forceChangePasswordNextSignIn=True
    - Requires consent approval (is_write_operation=True)
    - Supports verification via get_user tool

    Use Cases:
    - User forgot password
    - Account locked due to failed login attempts
    - Security incident requiring password reset
    """

    name = "reset_password"
    description = (
        "Reset a user's password in Azure Active Directory. "
        "User will be required to change the temporary password on next login. "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User ID (object ID) or UPN (email) to reset password for"
            },
            "temporary_password": {
                "type": "string",
                "description": (
                    "Optional: Temporary password (min 8 chars, complexity required). "
                    "If not provided, a secure random password will be generated."
                )
            }
        },
        "required": ["user_id"]
    }

    is_write_operation = True
    verification_tool_name = "get_user"

    def _generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Password length (default: 16)

        Returns:
            Secure random password meeting Azure complexity requirements
        """
        # Azure password requirements: uppercase, lowercase, digit, special char
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"

        # Ensure at least one of each required character type
        password = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]

        # Fill the rest randomly
        password += [secrets.choice(alphabet) for _ in range(length - 4)]

        # Shuffle to avoid predictable pattern
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    async def execute(
        self,
        user_id: str,
        temporary_password: str = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute password reset.

        Args:
            user_id: User object ID or UPN
            temporary_password: Optional temporary password (auto-generated if not provided)

        Returns:
            ToolResult with reset confirmation and temporary password
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # Generate password if not provided
            if not temporary_password:
                temporary_password = self._generate_secure_password()
                password_generated = True
            else:
                password_generated = False

            # Create password profile
            password_profile = PasswordProfile(
                password=temporary_password,
                force_change_password_next_sign_in=True  # Security best practice
            )

            # Update user with new password
            user = User()
            user.password_profile = password_profile

            logger.info(f"Resetting password for user: {user_id}")

            await client.users.by_user_id(user_id).patch(user)

            logger.info(f"Password reset successfully for user: {user_id}")

            result_data = {
                "id": user_id,
                "user_id": user_id,
                "temporary_password": temporary_password,
                "password_generated": password_generated,
                "force_change_on_next_login": True
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "password_reset",
                    "resource_type": "user",
                    "verification_hint": verification_hint,
                    "security_note": (
                        "User must change this temporary password on next login. "
                        "Share the temporary password securely (e.g., via phone, not email)."
                    )
                }
            )

        except Exception as e:
            logger.error(f"Failed to reset password for user {user_id}: {str(e)}")
            return await self._handle_azure_error(e)
