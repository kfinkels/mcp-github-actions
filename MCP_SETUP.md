# MCP Protocol Setup Guide

This guide shows how to use your MCP GitHub Actions server with various MCP clients.

## Prerequisites

1. **GitHub Token**: Get a personal access token from GitHub
   - Go to https://github.com/settings/tokens
   - Create a new token with `repo`, `read:user`, and `read:org` scopes
   - Copy the token

2. **MCP Server**: Your server should be installed and working
   ```bash
   cd /Users/keren.finkelstein/dev/mcp-github-actions
   poetry install
   ```

## Setup Options

### Option 1: Claude Desktop (Recommended)

**Step 1: Create Configuration File**

The configuration file is already created at:
`~/.config/claude-desktop/claude_desktop_config.json`

**Step 2: Add Your GitHub Token**

Edit the file and replace `your_github_token_here` with your actual token:

```json
{
  "mcpServers": {
    "github-actions": {
      "command": "poetry",
      "args": ["run", "python", "-m", "mcp_github_actions"],
      "cwd": "/Users/keren.finkelstein/dev/mcp-github-actions",
      "env": {
        "GITHUB_TOKEN": "ghp_your_actual_token_here"
      }
    }
  }
}
```

**Step 3: Restart Claude Desktop**

Close and reopen Claude Desktop application.

**Step 4: Verify Connection**

Look for the 🔧 (hammer) icon in Claude Desktop, which indicates MCP tools are available.

**Step 5: Use the Tools**

You can now ask Claude things like:
- "Get user activity for 'octocat' for the last 7 days"
- "Show me recent events for the user 'torvalds'"
- "What are the recent events for repository 'microsoft/vscode'?"
- "Get commits by user 'gvanrossum' in the last 30 days"

### Option 2: Using .env File (Alternative)

**Step 1: Create .env File**

```bash
cp .env.example .env
# Edit .env and add your token
```

**Step 2: Update Claude Desktop Config**

Use this configuration to use the .env file:

```json
{
  "mcpServers": {
    "github-actions": {
      "command": "poetry",
      "args": ["run", "python", "-m", "mcp_github_actions"],
      "cwd": "/Users/keren.finkelstein/dev/mcp-github-actions"
    }
  }
}
```

### Option 3: VS Code with MCP Extension

**Step 1: Install MCP Extension**

Install the MCP extension for VS Code (if available).

**Step 2: Configure**

Add this to your VS Code settings:

```json
{
  "mcp.servers": {
    "github-actions": {
      "command": "poetry",
      "args": ["run", "python", "-m", "mcp_github_actions"],
      "cwd": "/Users/keren.finkelstein/dev/mcp-github-actions",
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

### Option 4: Custom MCP Client

**Step 1: Install MCP Client Library**

```bash
pip install mcp
```

**Step 2: Create Custom Client**

```python
import asyncio
import subprocess
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    # Start the MCP server
    server_process = await stdio_client(
        "poetry", 
        ["run", "python", "-m", "mcp_github_actions"],
        cwd="/Users/keren.finkelstein/dev/mcp-github-actions",
        env={"GITHUB_TOKEN": "your_token_here"}
    )
    
    async with ClientSession(server_process[0], server_process[1]) as session:
        # Initialize the connection
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        print("Available tools:", [tool.name for tool in tools])
        
        # Call a tool
        result = await session.call_tool("get_user_activity", {
            "username": "octocat",
            "days": 7
        })
        print("Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools

Your MCP server provides these tools:

### 1. `get_user_events`
Get recent events for a GitHub user.

**Parameters:**
- `username` (string, required): GitHub username
- `limit` (integer, optional): Max events to return (default: 30)

**Example:**
```
Get user events for 'octocat' with limit 10
```

### 2. `get_user_activity`
Get comprehensive user activity including commits, issues, and PRs.

**Parameters:**
- `username` (string, required): GitHub username
- `days` (integer, optional): Days back to look (default: 7)

**Example:**
```
Get user activity for 'torvalds' for the last 14 days
```

### 3. `get_repository_events`
Get recent events for a GitHub repository.

**Parameters:**
- `owner` (string, required): Repository owner
- `repo` (string, required): Repository name
- `limit` (integer, optional): Max events to return (default: 30)

**Example:**
```
Get repository events for 'microsoft/vscode' with limit 15
```

### 4. `get_user_commits`
Get recent commits by a user across all repositories.

**Parameters:**
- `username` (string, required): GitHub username
- `since` (string, optional): ISO date string to get commits since
- `limit` (integer, optional): Max commits to return (default: 50)

**Example:**
```
Get commits by user 'gvanrossum' since '2024-01-01' with limit 25
```

## Troubleshooting

### Common Issues

1. **MCP Server Not Found**
   - Ensure you're in the correct directory
   - Check that Poetry is installed: `poetry --version`
   - Verify the server installs: `poetry install`

2. **GitHub Token Issues**
   - Verify token is valid: Test with `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`
   - Check token permissions include: `repo`, `read:user`, `read:org`

3. **Claude Desktop Not Showing Tools**
   - Restart Claude Desktop completely
   - Check the configuration file syntax is valid JSON
   - Look for error messages in Claude Desktop logs

4. **Connection Errors**
   - Ensure the server path is correct
   - Check that all dependencies are installed
   - Verify network connectivity

### Debug Commands

```bash
# Test server directly
poetry run python -m mcp_github_actions

# Test with our test script
python test_mcp_server.py

# Interactive testing
python test_mcp_server.py interactive

# Check configuration
cat ~/.config/claude-desktop/claude_desktop_config.json
```

## Security Notes

- **Never commit your GitHub token** to version control
- Store tokens in environment variables or `.env` files
- Use tokens with minimal required permissions
- Consider using GitHub Apps for production use
- Rotate tokens regularly

## Example Usage with Claude Desktop

Once set up, you can ask Claude:

**User Activity:**
```
"Can you get the user activity for 'octocat' for the last 7 days and summarize what they've been working on?"
```

**Repository Analysis:**
```
"Show me the recent events for the repository 'microsoft/vscode' and tell me what kind of activity is happening there."
```

**Developer Research:**
```
"Get the recent commits by 'gvanrossum' and analyze what projects he's been contributing to."
```

**Comparative Analysis:**
```
"Compare the activity of users 'torvalds' and 'gvanrossum' over the last 14 days."
```

The MCP protocol allows Claude to use your GitHub Actions server as a tool, giving it real-time access to GitHub data for analysis and insights! 