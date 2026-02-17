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
        self.timeout = 60.0  # Increased for slow search operations

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on the Obsidian server using JSON-RPC 2.0

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments as dictionary

        Returns:
            Tool response as dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # JSON-RPC 2.0 format with MCP tools/call wrapper
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 1
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()

                # Extract result from JSON-RPC response
                if "error" in result:
                    raise Exception(f"MCP error: {result['error']}")

                return result.get("result", {})
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
        Search notes in the vault using keyword search

        Args:
            query: Search query string (keyword)
            folder: Optional folder path to search in
            limit: Optional maximum number of results

        Returns:
            List of matching notes with metadata
        """
        args = {"keyword": query}  # obs_keyword_search uses 'keyword' not 'query'
        if folder:
            args["folder"] = folder
        if limit:
            args["limit"] = limit

        result = await self.call_tool("obs_keyword_search", args)

        # obs_keyword_search returns text with formatted results
        # We need to parse the note paths from the text response
        if isinstance(result, dict) and "content" in result:
            text = result["content"][0]["text"] if result["content"] else ""
            # Parse note paths from the markdown response
            notes = []
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("**Path:**"):
                    path = line.replace("**Path:**", "").strip()
                    # Get the title from previous line
                    title = ""
                    if i > 0:
                        title_line = lines[i-1]
                        if title_line.startswith("###"):
                            title = title_line.replace("###", "").strip().replace(".md", "").split(". ")[-1]
                    notes.append({"path": path, "title": title})
            return notes[:limit] if limit else notes

        return []

    async def read_note(self, path: str) -> Dict[str, Any]:
        """
        Read a note's content and metadata

        Args:
            path: Note path relative to vault root

        Returns:
            Note content and metadata with parsed frontmatter
        """
        result = await self.call_tool("obs_read_note", {"path": path})

        # obs_read_note returns text content, need to parse it
        if isinstance(result, dict) and "content" in result:
            text = result["content"][0]["text"] if result["content"] else ""

            # Parse YAML frontmatter
            frontmatter = {}
            content = text

            if text.startswith("# Content of"):
                # Remove the title line
                lines = text.split("\n", 1)
                if len(lines) > 1:
                    text = lines[1].strip()

            if text.startswith("---"):
                # Has frontmatter
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    yaml_str = parts[1].strip()
                    content = parts[2].strip()

                    # Parse YAML
                    try:
                        import yaml
                        frontmatter = yaml.safe_load(yaml_str) or {}
                    except Exception as e:
                        logger.warning(f"Failed to parse YAML frontmatter: {str(e)}")
                        # Fallback: simple key: value parsing
                        for line in yaml_str.split("\n"):
                            if ":" in line and not line.strip().startswith("#"):
                                key, value = line.split(":", 1)
                                frontmatter[key.strip()] = value.strip().strip('"').strip("'")

            return {
                "path": path,
                "content": content,
                "frontmatter": frontmatter,
                "raw": text
            }

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
            frontmatter: Optional frontmatter updates (note: not directly supported, merge manually)

        Returns:
            Update result
        """
        args = {"path": path}
        if content is not None:
            args["content"] = content
        # obs_update_note doesn't support separate frontmatter param
        # If frontmatter provided, need to merge it into content

        result = await self.call_tool("obs_update_note", args)
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
            frontmatter: Optional frontmatter (will be merged into content)

        Returns:
            Creation result
        """
        args = {"path": path, "content": content}
        # obs_create_note doesn't support separate frontmatter param
        # Frontmatter should be included in content

        result = await self.call_tool("obs_create_note", args)
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
        result = await self.call_tool("obs_append_note", {"path": path, "content": content})
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
            recursive: Whether to include subfolders (note: always recursive)

        Returns:
            List of notes with metadata
        """
        args = {}
        if folder:
            args["folder"] = folder
        # obs_list_notes doesn't have recursive param

        result = await self.call_tool("obs_list_notes", args)
        # Handle result format
        if isinstance(result, list):
            return result
        return result.get("notes", result.get("files", []))

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
        Check if MCP server is reachable using JSON-RPC ping

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            # JSON-RPC ping
            payload = {
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"MCP health check failed: {str(e)}")
            return False


# Global MCP client instance
mcp_client = MCPClient()
