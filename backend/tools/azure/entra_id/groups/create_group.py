"""
Create Group Tool
Creates a new group in Azure Active Directory (Entra ID).
"""
from typing import Optional, List
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.group import Group
import logging

logger = logging.getLogger(__name__)


class CreateGroupTool(AzureWriteTool):
    """
    Create a new group in Azure Active Directory.

    Supports both:
    - Security Groups (for access control and permissions)
    - Microsoft 365 Groups (for collaboration with email, SharePoint, Teams)

    Security Features:
    - Requires consent approval (is_write_operation=True)
    - Validates group type
    - Supports verification via get_group tool
    """

    name = "create_group"
    description = (
        "Create a new group in Azure Active Directory. "
        "Supports Security Groups (for access control) and Microsoft 365 Groups (for collaboration). "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "display_name": {
                "type": "string",
                "description": "Group display name (e.g., 'Finance Team')"
            },
            "mail_nickname": {
                "type": "string",
                "description": "Email alias for the group (e.g., 'finance-team')"
            },
            "description": {
                "type": "string",
                "description": "Optional: Group description"
            },
            "group_type": {
                "type": "string",
                "enum": ["security", "microsoft365"],
                "description": (
                    "Group type: 'security' for access control (default), "
                    "'microsoft365' for collaboration with email/Teams"
                ),
                "default": "security"
            },
            "mail_enabled": {
                "type": "boolean",
                "description": (
                    "Enable email for group (default: false for security groups, "
                    "true for Microsoft 365 groups)"
                )
            },
            "security_enabled": {
                "type": "boolean",
                "description": (
                    "Enable as security group (default: true for security groups, "
                    "false for Microsoft 365 groups)"
                )
            }
        },
        "required": ["display_name", "mail_nickname"]
    }

    is_write_operation = True
    verification_tool_name = "get_group"

    async def execute(
        self,
        display_name: str,
        mail_nickname: str,
        description: Optional[str] = None,
        group_type: str = "security",
        mail_enabled: Optional[bool] = None,
        security_enabled: Optional[bool] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute group creation.

        Args:
            display_name: Group display name
            mail_nickname: Email alias
            description: Optional group description
            group_type: 'security' or 'microsoft365'
            mail_enabled: Override mail enabled setting
            security_enabled: Override security enabled setting

        Returns:
            ToolResult with group details if successful
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # Determine group settings based on type
            if group_type.lower() == "security":
                # Security group defaults
                is_mail_enabled = mail_enabled if mail_enabled is not None else False
                is_security_enabled = security_enabled if security_enabled is not None else True
                group_types: List[str] = []
            elif group_type.lower() == "microsoft365":
                # Microsoft 365 group defaults
                is_mail_enabled = mail_enabled if mail_enabled is not None else True
                is_security_enabled = security_enabled if security_enabled is not None else False
                group_types = ["Unified"]  # "Unified" indicates Microsoft 365 group
            else:
                return ToolResult(
                    success=False,
                    error=f"Invalid group_type: {group_type}. Must be 'security' or 'microsoft365'."
                )

            # Build group object
            group = Group()
            group.display_name = display_name
            group.mail_nickname = mail_nickname
            group.mail_enabled = is_mail_enabled
            group.security_enabled = is_security_enabled
            group.group_types = group_types

            if description:
                group.description = description

            # Create group via Graph API
            logger.info(
                f"Creating {group_type} group: {display_name} "
                f"(mail_enabled={is_mail_enabled}, security_enabled={is_security_enabled})"
            )

            created_group = await client.groups.post(group)

            logger.info(
                f"Group created successfully: {created_group.display_name} "
                f"(ID: {created_group.id})"
            )

            result_data = {
                "id": created_group.id,
                "display_name": created_group.display_name,
                "mail_nickname": created_group.mail_nickname,
                "description": created_group.description,
                "mail": created_group.mail,
                "mail_enabled": created_group.mail_enabled,
                "security_enabled": created_group.security_enabled,
                "group_types": created_group.group_types,
                "group_type": group_type
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "created",
                    "resource_type": "group",
                    "verification_hint": verification_hint,
                    "note": (
                        f"Created {group_type} group. "
                        f"Use add_group_member to add users to this group."
                    )
                }
            )

        except Exception as e:
            logger.error(f"Failed to create group {display_name}: {str(e)}")
            return await self._handle_azure_error(e)
