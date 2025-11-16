"""Okta integration tools."""

from tools.okta.list_users import ListOktaUsersTool
from tools.okta.create_user import CreateOktaUserTool
from tools.registry import tool_registry

# Auto-register Okta tools
list_users_tool = ListOktaUsersTool()
create_user_tool = CreateOktaUserTool()

tool_registry.register(list_users_tool)
tool_registry.register(create_user_tool)

__all__ = ["ListOktaUsersTool", "CreateOktaUserTool"]
