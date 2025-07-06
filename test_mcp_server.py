#!/usr/bin/env python3
"""
Test script to interact with the MCP GitHub Actions server directly.
This bypasses the MCP protocol and calls the server functions directly.
"""

import os
import asyncio
import json
from datetime import datetime

# Set up environment
os.environ.setdefault('GITHUB_TOKEN', 'your_github_token_here')

# Import our server components
from src.mcp_github_actions.server import GitHubActionsServer
from src.mcp_github_actions.config import Config

async def test_server_functions():
    """Test the server functions directly."""
    
    print("🧪 Testing MCP GitHub Actions Server")
    print("=" * 50)
    
    # Check if GitHub token is set
    try:
        config = Config()
        if not config.validate_github_token():
            print("❌ GitHub token not found!")
            print("Please set GITHUB_TOKEN environment variable or create a .env file")
            return
        print(f"✅ GitHub token found: {config.github_token[:8]}...")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create server instance
    server = GitHubActionsServer()
    
    # Test 1: Get user events
    print("\n📊 Test 1: Get user events for 'kfinkels'")
    try:
        result = await server._get_user_events('kfinkels', 5)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"📋 Found {len(data)} events")
        for event in data[:2]:  # Show first 2
            print(f"  - {event['type']} on {event['repo']} at {event['created_at']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get user activity
    print("\n📊 Test 2: Get user activity for 'kfinkels'")
    try:
        result = await server._get_user_activity('kfinkels', 7)
        print("✅ Success!")
        data = json.loads(result[0].text)
        summary = data.get('summary', {})
        print(f"📈 Activity summary:")
        print(f"  - Total events: {summary.get('total_events', 0)}")
        print(f"  - Active repositories: {len(summary.get('repositories_active', []))}")
        print(f"  - Commits: {len(data.get('commits', []))}")
        print(f"  - Issues: {len(data.get('issues', []))}")
        print(f"  - Pull requests: {len(data.get('pull_requests', []))}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Get repository events
    print("\n📊 Test 3: Get repository events for 'kfinkels/prompt_eng'")
    try:
        result = await server._get_repository_events('kfinkels', 'prompt_eng', 3)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"📋 Found {len(data)} events")
        for event in data[:2]:  # Show first 2
            print(f"  - {event['type']} by {event['actor']} at {event['created_at']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get user commits
    print("\n📊 Test 4: Get user commits for 'kfinkels'")
    try:
        result = await server._get_user_commits('kfinkels', None, 5)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"📋 Found {len(data)} commits")
        for commit in data[:2]:  # Show first 2
            message = commit['message'].split('\n')[0]  # First line only
            print(f"  - {commit['sha'][:8]}: {message}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Testing completed!")

async def interactive_test():
    """Interactive testing mode."""
    print("\n🎮 Interactive Mode")
    print("Available commands:")
    print("1. get_user_events <username> [limit]")
    print("2. get_user_activity <username> [days]")
    print("3. get_repository_events <owner> <repo> [limit]")
    print("4. get_user_commits <username> [limit]")
    print("5. quit")
    
    server = GitHubActionsServer()
    
    while True:
        try:
            command = input("\n> ").strip()
            if not command:
                continue
                
            if command == 'quit':
                break
            
            parts = command.split()
            if len(parts) < 2:
                print("❌ Invalid command. Use: <command> <args>")
                continue
            
            cmd = parts[0]
            args = parts[1:]
            
            if cmd == 'get_user_events':
                username = args[0]
                limit = int(args[1]) if len(args) > 1 else 10
                result = await server._get_user_events(username, limit)
                data = json.loads(result[0].text)
                print(f"📋 Found {len(data)} events for {username}")
                for event in data[:5]:  # Show first 5
                    print(f"  - {event['type']} on {event['repo']} at {event['created_at']}")
            
            elif cmd == 'get_user_activity':
                username = args[0]
                days = int(args[1]) if len(args) > 1 else 7
                result = await server._get_user_activity(username, days)
                data = json.loads(result[0].text)
                summary = data.get('summary', {})
                print(f"📈 Activity for {username} (last {days} days):")
                print(f"  - Total events: {summary.get('total_events', 0)}")
                print(f"  - Active repositories: {len(summary.get('repositories_active', []))}")
                print(f"  - Commits: {len(data.get('commits', []))}")
                print(f"  - Issues: {len(data.get('issues', []))}")
                print(f"  - Pull requests: {len(data.get('pull_requests', []))}")
            
            elif cmd == 'get_repository_events':
                if len(args) < 2:
                    print("❌ Usage: get_repository_events <owner> <repo> [limit]")
                    continue
                owner, repo = args[0], args[1]
                limit = int(args[2]) if len(args) > 2 else 10
                result = await server._get_repository_events(owner, repo, limit)
                data = json.loads(result[0].text)
                print(f"📋 Found {len(data)} events for {owner}/{repo}")
                for event in data[:5]:  # Show first 5
                    print(f"  - {event['type']} by {event['actor']} at {event['created_at']}")
            
            elif cmd == 'get_user_commits':
                username = args[0]
                limit = int(args[1]) if len(args) > 1 else 10
                result = await server._get_user_commits(username, None, limit)
                data = json.loads(result[0].text)
                print(f"📋 Found {len(data)} commits for {username}")
                for commit in data[:5]:  # Show first 5
                    message = commit['message'].split('\n')[0]  # First line only
                    print(f"  - {commit['sha'][:8]}: {message}")
            
            else:
                print("❌ Unknown command")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    print("🐙 MCP GitHub Actions Server Tester")
    print("=" * 50)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'interactive':
        asyncio.run(interactive_test())
    else:
        asyncio.run(test_server_functions()) 