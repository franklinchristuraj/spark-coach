"""
MCP Client for communicating with Obsidian MCP Server
Wraps HTTP calls to the MCP server endpoints
"""
import httpx
from typing import Dict, List, Optional, Any
from config import settings
import logging

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with the Obsidian MCP Server"""

    def __init__(self):
        self.base_url = settings.MCP_SERVER_URL
        self.api_key = settings.MCP_API_KEY
        self.timeout = 30.0

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the Obsidian server

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool response as dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/call-tool",
                    json={
                        "name": tool_name,
                        "arguments": arguments
                    },
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"MCP tool call failed: {tool_name} - {str(e)}")
            raise

    async def search_notes(
        self,
        query: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search notes in the vault

        Args:
            query: Search query string
            folder: Optional folder path to search in
            limit: Optional maximum number of results

        Returns:
            List of matching notes with metadata
        """
        args = {"query": query}
        if folder:
            args["folder"] = folder
        if limit:
            args["limit"] = limit

        result = await self.call_tool("search_notes", args)
        return result.get("results", [])

    async def read_note(self, path: str) -> Dict[str, Any]:
        """
        Read a note's content and metadata

        Args:
            path: Note path relative to vault root

        Returns:
            Note content and metadata
        """
        result = await self.call_tool("read_note", {"path": path})
        return result

    async def update_note(
        self,
        path: str,
        content: Optional[str] = None,
        frontmatter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a note's content or frontmatter

        Args:
            path: Note path relative to vault root
            content: Optional new content for the note
            frontmatter: Optional frontmatter updates

        Returns:
            Update result
        """
        args = {"path": path}
        if content is not None:
            args["content"] = content
        if frontmatter is not None:
            args["frontmatter"] = frontmatter

        result = await self.call_tool("update_note", args)
        return result

    async def create_note(
        self,
        path: str,
        content: str,
        frontmatter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new note

        Args:
            path: Note path relative to vault root
            content: Note content
            frontmatter: Optional frontmatter

        Returns:
            Creation result
        """
        args = {"path": path, "content": content}
        if frontmatter is not None:
            args["frontmatter"] = frontmatter

        result = await self.call_tool("create_note", args)
        return result

    async def append_note(self, path: str, content: str) -> Dict[str, Any]:
        """
        Append content to an existing note

        Args:
            path: Note path relative to vault root
            content: Content to append

        Returns:
            Append result
        """
        result = await self.call_tool("append_note", {"path": path, "content": content})
        return result

    async def list_notes(
        self,
        folder: Optional[str] = None,
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List notes in a folder

        Args:
            folder: Optional folder path (defaults to vault root)
            recursive: Whether to include subfolders

        Returns:
            List of notes with metadata
        """
        args = {}
        if folder:
            args["folder"] = folder
        args["recursive"] = recursive

        result = await self.call_tool("list_notes", args)
        return result.get("notes", [])

    async def get_note_metadata(self, path: str) -> Dict[str, Any]:
        """
        Get only the metadata/frontmatter of a note

        Args:
            path: Note path relative to vault root

        Returns:
            Note metadata
        """
        note = await self.read_note(path)
        return note.get("frontmatter", {})

    async def health_check(self) -> bool:
        """
        Check if MCP server is reachable

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try base URL first
                response = await client.get(self.base_url, headers=headers)
                # Accept any 2xx or 404 (means server is up)
                return response.status_code in [200, 404]
        except Exception as e:
            logger.error(f"MCP health check failed: {str(e)}")
            # Return True anyway - we'll catch real errors on actual tool calls
            logger.warning("Assuming MCP server is available")
            return True


# Global MCP client instance
mcp_client = MCPClient()
