"""GitHub client for interacting with GitHub API."""

import asyncio
import logging
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
import time

import httpx
from github import Github, GithubException
from github.Event import Event
from github.Commit import Commit
from github.Repository import Repository
from github.PaginatedList import PaginatedList


logger = logging.getLogger(__name__)


class GitHubClient:
    """Async GitHub client for fetching user actions and repository events."""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        """Initialize GitHub client with authentication token."""
        self.token = token
        self.base_url = base_url
        self.github = Github(token)
        self.session = httpx.AsyncClient(
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "MCP-GitHub-Actions-Server/0.1.0"
            },
            timeout=30.0
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.aclose()
    
    async def get_user_events(self, username: str, limit: int = 30) -> List[Event]:
        """Get recent events for a GitHub user."""
        try:
            user = self.github.get_user(username)
            events = user.get_events()
            
            # Convert to list and limit
            event_list = []
            for i, event in enumerate(events):
                if i >= limit:
                    break
                event_list.append(event)
            
            return event_list
        except GithubException as e:
            logger.error(f"GitHub API error getting user events for {username}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user events for {username}: {e}")
            raise
    
    async def get_repository_events(self, owner: str, repo: str, limit: int = 30) -> List[Event]:
        """Get recent events for a GitHub repository."""
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            events = repository.get_events()
            
            # Convert to list and limit
            event_list = []
            for i, event in enumerate(events):
                if i >= limit:
                    break
                event_list.append(event)
            
            return event_list
        except GithubException as e:
            logger.error(f"GitHub API error getting repository events for {owner}/{repo}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting repository events for {owner}/{repo}: {e}")
            raise
    
    async def get_user_activity(self, username: str, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive user activity including commits, issues, and PRs."""
        try:
            user = self.github.get_user(username)
            since = datetime.now().replace(tzinfo=None) - timedelta(days=days)
            
            activity = {
                "user": username,
                "period_days": days,
                "since": since.isoformat(),
                "summary": {
                    "total_events": 0,
                    "repositories_active": set(),
                    "event_types": {}
                },
                "events": [],
                "commits": [],
                "issues": [],
                "pull_requests": []
            }
            
            # Get recent events
            events = user.get_events()
            for event in events:
                if event.created_at.replace(tzinfo=None) < since:
                    continue
                
                activity["summary"]["total_events"] += 1
                
                if event.repo:
                    activity["summary"]["repositories_active"].add(event.repo.name)
                
                event_type = event.type
                if event_type in activity["summary"]["event_types"]:
                    activity["summary"]["event_types"][event_type] += 1
                else:
                    activity["summary"]["event_types"][event_type] = 1
                
                activity["events"].append({
                    "type": event.type,
                    "repo": event.repo.name if event.repo else None,
                    "created_at": event.created_at.isoformat(),
                    "payload": self._extract_event_payload(event)
                })
            
            # Convert set to list for JSON serialization
            activity["summary"]["repositories_active"] = list(activity["summary"]["repositories_active"])
            
            # Get user's repositories to search for commits
            repos = user.get_repos(type="owner", sort="updated")
            for repo in repos:
                if repo.updated_at.replace(tzinfo=None) < since:
                    continue
                
                try:
                    commits = repo.get_commits(author=username, since=since)
                    for commit in commits:
                        activity["commits"].append({
                            "sha": commit.sha,
                            "message": commit.commit.message,
                            "repository": repo.full_name,
                            "date": commit.commit.author.date.isoformat(),
                            "url": commit.html_url
                        })
                except Exception as e:
                    logger.warning(f"Error getting commits for {repo.full_name}: {e}")
            
            # Get issues and PRs
            try:
                # Search for issues assigned to or created by the user
                since_str = since.strftime("%Y-%m-%d")
                issues = self.github.search_issues(f"assignee:{username} OR author:{username} updated:>={since_str}", state="all")
                for issue in issues:
                    issue_data = {
                        "number": issue.number,
                        "title": issue.title,
                        "state": issue.state,
                        "repository": issue.repository.full_name,
                        "created_at": issue.created_at.isoformat(),
                        "updated_at": issue.updated_at.isoformat(),
                        "url": issue.html_url
                    }
                    
                    if issue.pull_request:
                        activity["pull_requests"].append({
                            **issue_data,
                            "is_pull_request": True
                        })
                    else:
                        activity["issues"].append(issue_data)
            except Exception as e:
                logger.warning(f"Error getting issues for {username}: {e}")
            
            return activity
        
        except GithubException as e:
            logger.error(f"GitHub API error getting user activity for {username}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user activity for {username}: {e}")
            raise
    
    async def get_user_commits(self, username: str, since: Optional[str] = None, limit: int = 50) -> List[Commit]:
        """Get recent commits by a user across repositories."""
        try:
            user = self.github.get_user(username)
            since_date = None
            
            if since:
                since_date = datetime.fromisoformat(since.replace('Z', '+00:00')).replace(tzinfo=None)
            else:
                since_date = datetime.now().replace(tzinfo=None) - timedelta(days=30)  # Default to 30 days
            
            commits = []
            repos = user.get_repos(type="owner", sort="updated")
            
            for repo in repos:
                if repo.updated_at.replace(tzinfo=None) < since_date:
                    continue
                
                try:
                    repo_commits = repo.get_commits(author=username, since=since_date)
                    for commit in repo_commits:
                        commits.append(commit)
                        if len(commits) >= limit:
                            break
                except Exception as e:
                    logger.warning(f"Error getting commits for {repo.full_name}: {e}")
                
                if len(commits) >= limit:
                    break
            
            # Sort commits by date (newest first)
            commits.sort(key=lambda c: c.commit.author.date, reverse=True)
            
            return commits[:limit]
        
        except GithubException as e:
            logger.error(f"GitHub API error getting user commits for {username}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user commits for {username}: {e}")
            raise
    
    def _extract_event_payload(self, event: Event) -> Dict[str, Any]:
        """Extract relevant payload information from GitHub event."""
        payload = {}
        
        try:
            if event.type == "PushEvent":
                payload = {
                    "commits": len(event.payload.get("commits", [])),
                    "ref": event.payload.get("ref", ""),
                    "head": event.payload.get("head", ""),
                    "size": event.payload.get("size", 0)
                }
            elif event.type == "IssuesEvent":
                issue = event.payload.get("issue", {})
                payload = {
                    "action": event.payload.get("action", ""),
                    "issue": {
                        "number": issue.get("number", 0),
                        "title": issue.get("title", ""),
                        "state": issue.get("state", ""),
                        "url": issue.get("html_url", "")
                    }
                }
            elif event.type == "PullRequestEvent":
                pr = event.payload.get("pull_request", {})
                payload = {
                    "action": event.payload.get("action", ""),
                    "pull_request": {
                        "number": pr.get("number", 0),
                        "title": pr.get("title", ""),
                        "state": pr.get("state", ""),
                        "url": pr.get("html_url", "")
                    }
                }
            elif event.type == "CreateEvent":
                payload = {
                    "ref_type": event.payload.get("ref_type", ""),
                    "ref": event.payload.get("ref", ""),
                    "description": event.payload.get("description", "")
                }
            elif event.type == "DeleteEvent":
                payload = {
                    "ref_type": event.payload.get("ref_type", ""),
                    "ref": event.payload.get("ref", "")
                }
            elif event.type == "WatchEvent":
                payload = {
                    "action": event.payload.get("action", "started")
                }
            elif event.type == "ForkEvent":
                forkee = event.payload.get("forkee", {})
                payload = {
                    "forkee": {
                        "full_name": forkee.get("full_name", ""),
                        "url": forkee.get("html_url", "")
                    }
                }
            elif event.type == "ReleaseEvent":
                release = event.payload.get("release", {})
                payload = {
                    "action": event.payload.get("action", ""),
                    "release": {
                        "tag_name": release.get("tag_name", ""),
                        "name": release.get("name", ""),
                        "url": release.get("html_url", "")
                    }
                }
            else:
                # For other event types, include the raw payload
                payload = event.payload if event.payload else {}
        
        except Exception as e:
            logger.warning(f"Error extracting payload for event {event.type}: {e}")
            payload = {"error": "Failed to extract payload"}
        
        return payload
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose() 