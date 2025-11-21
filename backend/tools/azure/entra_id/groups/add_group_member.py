"""
Add Group Member Tool
Adds a user to a group in Azure Active Directory (Entra ID).
"""
from tools.azure.base import AzureWriteTool, ToolResult
from msgraph.generated.models.reference_create import ReferenceCreate
import logging

logger = logging.getLogger(__name__)


class AddGroupMemberTool(AzureWriteTool):
    """
    Add a user to a group in Azure Active Directory.

    This tool manages group membership for:
    - Security groups (access control)
    - Microsoft 365 groups (collaboration)

    Security Features:
    - Requires consent approval (is_write_operation=True)
    - Validates user and group existence
    - Supports verification via get_group tool

    Use Cases:
    - Grant user access to resources (via security group)
    - Add user to team collaboration group
    - Bulk user provisioning workflows
    """

    name = "add_group_member"
    description = (
        "Add a user as a member of a group in Azure Active Directory. "
        "Works with both security groups and Microsoft 365 groups. "
        "This operation requires approval."
    )
    parameters = {
        "type": "object",
        "properties": {
            "group_id": {
                "type": "string",
                "description": "Group object ID (GUID)"
            },
            "user_id": {
                "type": "string",
                "description": "User object ID (GUID) or User Principal Name (email)"
            }
        },
        "required": ["group_id", "user_id"]
    }

    is_write_operation = True
    verification_tool_name = "get_group"

    async def execute(
        self,
        group_id: str,
        user_id: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute add group member operation.

        Args:
            group_id: Group object ID
            user_id: User object ID or UPN

        Returns:
            ToolResult with membership confirmation
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            # First, verify the user exists and get their object ID
            try:
                user = await client.users.by_user_id(user_id).get()
                user_object_id = user.id
                user_upn = user.user_principal_name
                user_display_name = user.display_name
            except Exception as user_error:
                logger.error(f"User not found: {user_id}")
                return ToolResult(
                    success=False,
                    error=f"User not found: {user_id}. Please verify the user exists.",
                    metadata={"user_id": user_id}
                )

            # Verify the group exists
            try:
                group = await client.groups.by_group_id(group_id).get()
                group_display_name = group.display_name
            except Exception as group_error:
                logger.error(f"Group not found: {group_id}")
                return ToolResult(
                    success=False,
                    error=f"Group not found: {group_id}. Please verify the group exists.",
                    metadata={"group_id": group_id}
                )

            # Create reference to user
            # Microsoft Graph requires a reference object with the user's directory object URL
            reference = ReferenceCreate()
            reference.odata_id = f"https://graph.microsoft.com/v1.0/directoryObjects/{user_object_id}"

            # Add user to group
            logger.info(
                f"Adding user {user_upn} ({user_object_id}) "
                f"to group {group_display_name} ({group_id})"
            )

            await client.groups.by_group_id(group_id).members.ref.post(reference)

            logger.info(
                f"User {user_upn} successfully added to group {group_display_name}"
            )

            result_data = {
                "id": group_id,
                "group_id": group_id,
                "group_name": group_display_name,
                "user_id": user_object_id,
                "user_principal_name": user_upn,
                "user_display_name": user_display_name,
                "membership_added": True
            }

            # Generate verification hint
            verification_hint = self.get_verification_hint(result_data)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "action": "member_added",
                    "resource_type": "group",
                    "verification_hint": verification_hint,
                    "note": (
                        f"User {user_display_name} ({user_upn}) added to group "
                        f"{group_display_name}. Changes may take a few minutes to propagate."
                    )
                }
            )

        except Exception as e:
            # Check for duplicate membership error
            error_str = str(e)
            if "already exist" in error_str.lower() or "already a member" in error_str.lower():
                logger.info(f"User {user_id} is already a member of group {group_id}")
                return ToolResult(
                    success=True,
                    data={
                        "group_id": group_id,
                        "user_id": user_id,
                        "membership_added": False,
                        "already_member": True
                    },
                    metadata={
                        "action": "no_change",
                        "note": "User is already a member of this group"
                    }
                )

            logger.error(f"Failed to add user {user_id} to group {group_id}: {str(e)}")
            return await self._handle_azure_error(e)
