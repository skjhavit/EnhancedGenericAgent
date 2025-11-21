"""Azure Active Directory (Entra ID) Management Tools."""
from .users import CreateUserTool, GetUserTool, ResetPasswordTool
from .groups import CreateGroupTool, GetGroupTool, AddGroupMemberTool
from .apps import (
    CreateAppRegistrationTool,
    GetAppRegistrationTool,
    AddRedirectUriTool,
    CreateClientSecretTool,
)

__all__ = [
    # User Management
    "CreateUserTool",
    "GetUserTool",
    "ResetPasswordTool",
    # Group Management
    "CreateGroupTool",
    "GetGroupTool",
    "AddGroupMemberTool",
    # App Registration Management
    "CreateAppRegistrationTool",
    "GetAppRegistrationTool",
    "AddRedirectUriTool",
    "CreateClientSecretTool",
]
