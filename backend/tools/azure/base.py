"""
Azure Tool Base Classes
Provides common functionality for all Azure-related tools.
"""
from typing import Optional, Dict, Any
from tools.base import BaseTool, ToolResult
from .auth.credential_manager import AzureCredentialManager
from msgraph import GraphServiceClient
import logging

logger = logging.getLogger(__name__)


class AzureBaseTool(BaseTool):
    """
    Base class for all Azure tools.

    Provides:
    - Common authentication via credential manager
    - Standardized error handling for Azure API errors
    - Consistent logging
    """

    def get_graph_client(self) -> GraphServiceClient:
        """
        Get authenticated Microsoft Graph API client.

        Returns:
            GraphServiceClient: Authenticated client

        Raises:
            ValueError: If Azure credentials are not configured
        """
        return AzureCredentialManager.get_graph_client()

    async def _handle_azure_error(self, error: Exception) -> ToolResult:
        """
        Standardized error handling for Azure API errors.

        Maps common Azure error codes to user-friendly messages.

        Args:
            error: Exception from Azure API

        Returns:
            ToolResult with success=False and friendly error message
        """
        # Common Azure AD / Graph API error codes
        error_map = {
            "Request_ResourceNotFound": "The requested resource (user/group/app) doesn't exist in Azure AD",
            "Authorization_RequestDenied": "Insufficient permissions to perform this operation. Check service principal permissions.",
            "Request_MultipleObjectsWithSameKeyValue": "A resource with this identifier already exists",
            "InvalidAuthenticationToken": "Authentication failed. Check Azure credentials configuration.",
            "Directory_QuotaExceeded": "Directory quota exceeded. Contact your Azure administrator.",
            "Request_BadRequest": "Invalid request parameters",
            "Authentication_MissingOrMalformed": "Azure credentials are missing or malformed",
            "Directory_ObjectNotFound": "Object not found in directory",
            "Request_ThrottledPermanently": "Too many requests. Please try again later.",
            "InvalidRequest": "The request is invalid. Check parameters.",
        }

        # Try to extract error code from exception
        error_code = None
        error_message = str(error)

        # Check if error has a 'code' attribute (common in Azure SDK exceptions)
        if hasattr(error, 'code'):
            error_code = error.code
        # Check if error message contains error code pattern
        elif ':' in error_message:
            parts = error_message.split(':', 1)
            if len(parts) > 0:
                potential_code = parts[0].strip()
                if potential_code in error_map:
                    error_code = potential_code

        # Get friendly message or use original error
        friendly_message = error_map.get(error_code, error_message)

        logger.error(
            f"Azure API error in {self.name}: {error_code or 'UNKNOWN'} - {error_message}"
        )

        return ToolResult(
            success=False,
            error=friendly_message,
            metadata={
                "azure_error_code": error_code,
                "original_error": error_message,
                "tool": self.name
            }
        )

    async def _check_credentials(self) -> Optional[ToolResult]:
        """
        Check if Azure credentials are configured.

        Returns:
            None if credentials are configured, ToolResult with error if not
        """
        if not AzureCredentialManager.is_configured():
            return ToolResult(
                success=False,
                error=(
                    "Azure credentials not configured. "
                    "Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET "
                    "environment variables."
                ),
                metadata={"tool": self.name}
            )
        return None


class AzureWriteTool(AzureBaseTool):
    """
    Base class for Azure write operations (create, update, delete).

    Automatically:
    - Marks as write operation (triggers consent flow)
    - Provides verification metadata
    - Suggests corresponding read tool for verification
    """

    is_write_operation = True
    verification_tool_name: Optional[str] = None  # e.g., "get_user"

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute write operation.

        Subclasses should override this method and call super().execute()
        to ensure credential checks.
        """
        # Check credentials before executing
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        # Subclass implements actual logic
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )

    def get_verification_hint(self, result_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate hint for verification step.

        Args:
            result_data: Data returned from execute()

        Returns:
            Hint message for LLM to verify the operation
        """
        if not self.verification_tool_name:
            return None

        resource_id = result_data.get("id") or result_data.get("user_id") or result_data.get("group_id")

        if resource_id:
            return (
                f"VERIFICATION REQUIRED: Call {self.verification_tool_name}(id='{resource_id}') "
                f"to confirm this operation succeeded and attributes match expectations."
            )

        return None


class AzureReadTool(AzureBaseTool):
    """
    Base class for Azure read operations (get, list).

    Characteristics:
    - No consent required (is_write_operation=False)
    - Used for investigation and verification
    """

    is_write_operation = False

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute read operation.

        Subclasses should override this method and call super().execute()
        to ensure credential checks.
        """
        # Check credentials before executing
        cred_check = await self._check_credentials()
        if cred_check:
            return cred_check

        # Subclass implements actual logic
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement execute() method"
        )
