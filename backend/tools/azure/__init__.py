"""
Azure Tools for Agent-as-a-Service Platform

This module provides Azure Active Directory (Entra ID) management capabilities
for the Azure Workforce Admin Agent.

Phase 1 Tools (Foundation):
- User Management: create_user, get_user, reset_password
- Group Management: create_group, get_group, add_group_member

Phase 2 Tools (Verification + App Registration):
- App Registration: create_app_registration, get_app_registration
- App Configuration: add_redirect_uri, create_client_secret

All tools follow the platform's tool registry pattern and integrate with
the Human-in-the-Loop consent flow for write operations.
"""
from .entra_id import (
    # User Management
    CreateUserTool,
    GetUserTool,
    ResetPasswordTool,
    # Group Management
    CreateGroupTool,
    GetGroupTool,
    AddGroupMemberTool,
    # App Registration Management
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
