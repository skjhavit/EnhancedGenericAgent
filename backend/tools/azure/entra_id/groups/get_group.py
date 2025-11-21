"""
Get Group Tool
Retrieves group details from Azure Active Directory (Entra ID).
"""
from tools.azure.base import AzureReadTool, ToolResult
import logging

logger = logging.getLogger(__name__)


class GetGroupTool(AzureReadTool):
    """
    Retrieve group details from Azure Active Directory.

    This tool is used for:
    - Verification after group creation/updates
    - Investigation when troubleshooting access issues
    - General group information lookup

    No consent required (read operation).
    """

    name = "get_group"
    description = (
        "Retrieve detailed information about a group from Azure Active Directory. "
        "Use for verification after creating/updating groups or for troubleshooting. "
        "Accepts either group ID (object ID) or display name."
    )
    parameters = {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "Group identifier: object ID (GUID) or display name"
            }
        },
        "required": ["id"]
    }

    is_write_operation = False

    async def execute(self, id: str, **kwargs) -> ToolResult:
        """
        Execute group retrieval.

        Args:
            id: Group object ID or display name

        Returns:
            ToolResult with group details if found
        """
        # Check credentials first
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        try:
            client = self.get_graph_client()

            logger.info(f"Retrieving group: {id}")

            # Get group by ID
            group = await client.groups.by_group_id(id).get()

            if not group:
                return ToolResult(
                    success=False,
                    error=f"Group not found: {id}",
                    metadata={"queried_id": id}
                )

            logger.info(f"Group retrieved: {group.display_name} (ID: {group.id})")

            # Determine group type
            if group.group_types and "Unified" in group.group_types:
                group_type = "microsoft365"
            else:
                group_type = "security"

            # Return comprehensive group data
            result_data = {
                "id": group.id,
                "display_name": group.display_name,
                "description": group.description,
                "mail": group.mail,
                "mail_nickname": group.mail_nickname,
                "mail_enabled": group.mail_enabled,
                "security_enabled": group.security_enabled,
                "group_types": group.group_types,
                "group_type": group_type,
                "created_date_time": str(group.created_date_time) if group.created_date_time else None,
                "visibility": group.visibility,
                "membership_rule": group.membership_rule,
                "membership_rule_processing_state": group.membership_rule_processing_state
            }

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "resource_type": "group",
                    "queried_id": id
                }
            )

        except Exception as e:
            logger.error(f"Failed to retrieve group {id}: {str(e)}")
            return await self._handle_azure_error(e)
