"""Simple note-taking tool to demonstrate write operations with consent."""

from typing import Dict, Any
from tools.base import BaseTool, ToolResult


# In-memory storage for demonstration (would be database in production)
_notes_storage: Dict[str, str] = {}


class CreateNoteTool(BaseTool):
    """
    Tool to create a new note.

    This demonstrates a write operation that requires user consent.
    """

    name = "create_note"
    description = "Create a new note with a title and content. This will store the note in the system."
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the note"
            },
            "content": {
                "type": "string",
                "description": "Content/body of the note"
            }
        },
        "required": ["title", "content"]
    }
    is_write_operation = True  # Requires consent!

    async def execute(self, title: str, content: str) -> ToolResult:
        """
        Create a new note.

        Args:
            title: Note title
            content: Note content

        Returns:
            ToolResult with the created note
        """
        try:
            if not title or not title.strip():
                return ToolResult(
                    success=False,
                    error="Note title cannot be empty"
                )

            # Store the note
            _notes_storage[title] = content

            return ToolResult(
                success=True,
                data={
                    "title": title,
                    "content": content,
                    "message": f"Note '{title}' created successfully"
                },
                metadata={"operation": "create", "note_count": len(_notes_storage)}
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error creating note: {str(e)}"
            )


class ListNotesTool(BaseTool):
    """
    Tool to list all notes.

    This is a read-only operation.
    """

    name = "list_notes"
    description = "List all stored notes with their titles and content."
    parameters = {
        "type": "object",
        "properties": {}
    }
    is_write_operation = False  # Read-only

    async def execute(self) -> ToolResult:
        """
        List all notes.

        Returns:
            ToolResult with list of all notes
        """
        try:
            if not _notes_storage:
                return ToolResult(
                    success=True,
                    data={
                        "notes": [],
                        "count": 0,
                        "message": "No notes found"
                    }
                )

            notes = [
                {"title": title, "content": content}
                for title, content in _notes_storage.items()
            ]

            return ToolResult(
                success=True,
                data={
                    "notes": notes,
                    "count": len(notes)
                }
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error listing notes: {str(e)}"
            )
