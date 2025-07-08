# MCP GitHub Actions

A Model Context Protocol (MCP) server for reading GitHub user actions and repository events. This server provides tools to fetch and analyze user activity across GitHub repositories.

## Features

- **User Events**: Get recent events for any GitHub user
- **Repository Events**: Get recent events for any GitHub repository
- **User Activity**: Get comprehensive user activity including commits, issues, and PRs
- **User Commits**: Get recent commits by a user across all repositories
- **Tech Stack Analysis**: Analyze user's commits to extract tech stack, programming languages, and change patterns
- **Work Experience Generator**: Generate comprehensive LinkedIn/resume-ready work experience profiles from GitHub activity
- **Structured Data**: Returns well-formatted JSON data for easy analysis

## Installation

1. **Prerequisites**:
   - Python 3.11 or higher
   - Poetry package manager

2. **Clone and install**:
   ```bash
   git clone <your-repo-url>
   cd mcp-github-actions
   poetry install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your GitHub token
   ```

## Configuration

### GitHub Token

You need a GitHub Personal Access Token to use this server:

1. Go to [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name like "MCP GitHub Actions"
4. Select the following scopes:
   - `repo` (for repository access)
   - `read:user` (for user information)
   - `read:org` (for organization information)
5. Click "Generate token"
6. Copy the token and add it to your `.env` file:
   ```
   GITHUB_TOKEN=your_token_here
   ```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub personal access token | **Required** |
| `GITHUB_API_URL` | GitHub API base URL | `https://api.github.com` |
| `RATE_LIMIT_RETRIES` | Number of retries for rate limit errors | `3` |
| `REQUEST_TIMEOUT` | Request timeout in seconds | `30` |
| `MAX_EVENTS_PER_REQUEST` | Maximum events per request | `100` |
| `CACHE_TTL` | Cache TTL in seconds | `300` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Usage

### Running the Server

```bash
# Using Poetry
poetry run python -m mcp_github_actions

# Or activate the virtual environment first
poetry shell
python -m mcp_github_actions
```

### MCP Tools

The server provides the following tools:

#### `get_user_events`

Get recent events for a GitHub user.

**Parameters**:
- `username` (string, required): GitHub username
- `limit` (integer, optional): Maximum number of events (default: 30)

**Example**:
```json
{
  "name": "get_user_events",
  "arguments": {
    "username": "octocat",
    "limit": 10
  }
}
```

#### `get_repository_events`

Get recent events for a GitHub repository.

**Parameters**:
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `limit` (integer, optional): Maximum number of events (default: 30)

**Example**:
```json
{
  "name": "get_repository_events",
  "arguments": {
    "owner": "microsoft",
    "repo": "vscode",
    "limit": 20
  }
}
```

#### `get_user_activity`

Get comprehensive user activity including commits, issues, and PRs.

**Parameters**:
- `username` (string, required): GitHub username
- `days` (integer, optional): Number of days back to look (default: 7)

**Example**:
```json
{
  "name": "get_user_activity",
  "arguments": {
    "username": "octocat",
    "days": 14
  }
}
```

#### `get_user_commits`

Get recent commits by a user across all repositories.

**Parameters**:
- `username` (string, required): GitHub username
- `since` (string, optional): ISO date string to get commits since
- `limit` (integer, optional): Maximum number of commits (default: 50)

**Example**:
```json
{
  "name": "get_user_commits",
  "arguments": {
    "username": "octocat",
    "since": "2024-01-01T00:00:00Z",
    "limit": 25
  }
}
```

## Data Structure

### User Events

Each event includes:
- `type`: Event type (PushEvent, IssuesEvent, PullRequestEvent, etc.)
- `actor`: Username of the actor
- `repo`: Repository name
- `created_at`: Event timestamp
- `payload`: Event-specific data

### User Activity

Comprehensive activity report including:
- `summary`: Activity statistics
- `events`: Recent events
- `commits`: Recent commits
- `issues`: Recent issues
- `pull_requests`: Recent pull requests

## Development

### Project Structure

```
mcp-github-actions/
├── src/
│   └── mcp_github_actions/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py          # Main MCP server
│       ├── github_client.py   # GitHub API client
│       └── config.py          # Configuration management
├── pyproject.toml
├── README.md
└── .env.example
```

### Running Tests

```bash
# Install development dependencies
poetry install --with dev

# Run tests (when implemented)
poetry run pytest
```

### Code Quality

The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

## Rate Limiting

The GitHub API has rate limits:
- **Authenticated requests**: 5,000 requests per hour
- **Unauthenticated requests**: 60 requests per hour

This server automatically handles rate limiting with retries and respects GitHub's rate limits.

## Error Handling

The server provides comprehensive error handling:
- Invalid GitHub tokens
- Rate limit exceeded
- Repository/user not found
- Network connectivity issues
- Invalid parameters

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **"GitHub token not found"**: Make sure you've set the `GITHUB_TOKEN` environment variable
2. **"Rate limit exceeded"**: Wait for the rate limit to reset or use a different token
3. **"User not found"**: Check that the username is correct and the user exists
4. **"Repository not found"**: Check that the repository exists and is accessible

### Getting Help

- Check the logs for detailed error messages
- Verify your GitHub token has the required permissions
- Ensure your network connection is stable
- Check GitHub's status page for API issues 