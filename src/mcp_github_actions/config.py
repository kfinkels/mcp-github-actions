"""Configuration management for MCP GitHub Actions server."""

import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the GitHub Actions MCP server."""
    
    github_token: str = Field(
        ...,
        description="GitHub personal access token for API access",
        env="GITHUB_TOKEN"
    )
    
    github_api_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
        env="GITHUB_API_URL"
    )
    
    rate_limit_retries: int = Field(
        default=3,
        description="Number of retries for rate limit errors",
        env="RATE_LIMIT_RETRIES"
    )
    
    request_timeout: int = Field(
        default=30,
        description="Request timeout in seconds",
        env="REQUEST_TIMEOUT"
    )
    
    max_events_per_request: int = Field(
        default=100,
        description="Maximum number of events to fetch per request",
        env="MAX_EVENTS_PER_REQUEST"
    )
    
    cache_ttl: int = Field(
        default=300,
        description="Cache TTL in seconds (5 minutes default)",
        env="CACHE_TTL"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        env="LOG_LEVEL"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls()
    
    def validate_github_token(self) -> bool:
        """Validate that GitHub token is present and not empty."""
        return bool(self.github_token and self.github_token.strip())
    
    def get_github_headers(self) -> dict:
        """Get headers for GitHub API requests."""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-GitHub-Actions-Server/0.1.0"
        } 