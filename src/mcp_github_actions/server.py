"""MCP server for reading GitHub user actions."""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)
from pydantic import BaseModel, Field
from github import Github
from github.Repository import Repository
from github.PaginatedList import PaginatedList
from github.Event import Event
from github.Commit import Commit
from github.Issue import Issue
from github.PullRequest import PullRequest

from .github_client import GitHubClient
from .config import Config


class GitHubActionsTool(BaseModel):
    """Tool for getting GitHub user actions."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")


class GitHubActionsServer:
    """MCP server for GitHub actions."""
    
    def __init__(self):
        self.config = Config()
        self.github_client = GitHubClient(self.config.github_token)
        self.server = Server("github-actions-server")
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up the available tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_user_events",
                    description="Get recent events for a GitHub user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub username to get events for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of events to return (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["username"]
                    }
                ),
                Tool(
                    name="get_repository_events",
                    description="Get recent events for a GitHub repository",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "owner": {
                                "type": "string",
                                "description": "Repository owner (username or organization)"
                            },
                            "repo": {
                                "type": "string",
                                "description": "Repository name"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of events to return (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["owner", "repo"]
                    }
                ),
                Tool(
                    name="get_user_activity",
                    description="Get comprehensive user activity including commits, issues, and PRs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub username to get activity for"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days back to look for activity (default: 7)",
                                "default": 7
                            }
                        },
                        "required": ["username"]
                    }
                ),
                Tool(
                    name="get_user_commits",
                    description="Get recent commits by a user across all repositories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub username to get commits for"
                            },
                            "since": {
                                "type": "string",
                                "description": "ISO date string to get commits since (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of commits to return (default: 50)",
                                "default": 50
                            }
                        },
                        "required": ["username"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool calls."""
            
            if name == "get_user_events":
                return await self._get_user_events(
                    arguments["username"],
                    arguments.get("limit", 30)
                )
            elif name == "get_repository_events":
                return await self._get_repository_events(
                    arguments["owner"],
                    arguments["repo"],
                    arguments.get("limit", 30)
                )
            elif name == "get_user_activity":
                return await self._get_user_activity(
                    arguments["username"],
                    arguments.get("days", 7)
                )
            elif name == "get_user_commits":
                return await self._get_user_commits(
                    arguments["username"],
                    arguments.get("since"),
                    arguments.get("limit", 50)
                )
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _get_user_events(self, username: str, limit: int) -> List[TextContent]:
        """Get recent events for a GitHub user."""
        try:
            events = await self.github_client.get_user_events(username, limit)
            
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "type": event.type,
                    "actor": event.actor.login if event.actor else "Unknown",
                    "repo": event.repo.name if event.repo else "Unknown",
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "payload": self._format_event_payload(event)
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(formatted_events, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting user events: {str(e)}"
            )]
    
    async def _get_repository_events(self, owner: str, repo: str, limit: int) -> List[TextContent]:
        """Get recent events for a GitHub repository."""
        try:
            events = await self.github_client.get_repository_events(owner, repo, limit)
            
            formatted_events = []
            for event in events:
                formatted_events.append({
                    "type": event.type,
                    "actor": event.actor.login if event.actor else "Unknown",
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "payload": self._format_event_payload(event)
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(formatted_events, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting repository events: {str(e)}"
            )]
    
    async def _get_user_activity(self, username: str, days: int) -> List[TextContent]:
        """Get comprehensive user activity."""
        try:
            activity = await self.github_client.get_user_activity(username, days)
            
            return [TextContent(
                type="text",
                text=json.dumps(activity, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting user activity: {str(e)}"
            )]
    
    async def _get_user_commits(self, username: str, since: Optional[str], limit: int) -> List[TextContent]:
        """Get recent commits by a user."""
        try:
            commits = await self.github_client.get_user_commits(username, since, limit)
            
            formatted_commits = []
            for commit in commits:
                formatted_commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date.isoformat()
                    },
                    "repository": commit.repository.full_name if hasattr(commit, 'repository') else "Unknown",
                    "url": commit.html_url
                })
            
            return [TextContent(
                type="text",
                text=json.dumps(formatted_commits, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting user commits: {str(e)}"
            )]
    
    def _format_event_payload(self, event: Event) -> Dict[str, Any]:
        """Format event payload for display."""
        payload = {}
        
        if event.type == "PushEvent":
            payload = {
                "commits": len(event.payload.get("commits", [])),
                "ref": event.payload.get("ref", "Unknown"),
                "head": event.payload.get("head", "Unknown")
            }
        elif event.type == "IssuesEvent":
            payload = {
                "action": event.payload.get("action", "Unknown"),
                "issue_number": event.payload.get("issue", {}).get("number", "Unknown"),
                "issue_title": event.payload.get("issue", {}).get("title", "Unknown")
            }
        elif event.type == "PullRequestEvent":
            payload = {
                "action": event.payload.get("action", "Unknown"),
                "pr_number": event.payload.get("pull_request", {}).get("number", "Unknown"),
                "pr_title": event.payload.get("pull_request", {}).get("title", "Unknown")
            }
        elif event.type == "CreateEvent":
            payload = {
                "ref_type": event.payload.get("ref_type", "Unknown"),
                "ref": event.payload.get("ref", "Unknown")
            }
        elif event.type == "DeleteEvent":
            payload = {
                "ref_type": event.payload.get("ref_type", "Unknown"),
                "ref": event.payload.get("ref", "Unknown")
            }
        elif event.type == "WatchEvent":
            payload = {
                "action": event.payload.get("action", "Unknown")
            }
        elif event.type == "ForkEvent":
            payload = {
                "forkee": event.payload.get("forkee", {}).get("full_name", "Unknown")
            }
        
        return payload
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="github-actions-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point."""
    server = GitHubActionsServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main()) 