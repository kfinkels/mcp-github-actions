#!/usr/bin/env python3
"""
Example usage of the MCP GitHub Actions server.

This script demonstrates how to use the GitHub Actions MCP server
to fetch user events and activity.

Make sure to:
1. Set up your .env file with GITHUB_TOKEN
2. Install dependencies: poetry install
3. Run this script: python example_usage.py
"""

import os
import asyncio
import json
from datetime import datetime

# Make sure we can import our modules
try:
    from src.mcp_github_actions.github_client import GitHubClient
    from src.mcp_github_actions.config import Config
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the project root directory and have installed dependencies with 'poetry install'")
    exit(1)

async def main():
    """Example usage of the GitHub client."""
    
    # Load configuration
    try:
        config = Config()
        if not config.validate_github_token():
            print("❌ GitHub token not found or invalid!")
            print("Please set GITHUB_TOKEN in your .env file")
            print("See README.md for instructions on how to get a GitHub token")
            return
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Make sure you have a .env file with GITHUB_TOKEN set")
        return
    
    print("✅ Configuration loaded successfully")
    print(f"🔑 Using GitHub token: {config.github_token[:8]}...")
    
    # Create GitHub client
    github_client = GitHubClient(config.github_token)
    
    print("\n🚀 Testing GitHub client...")
    
    # Test 1: Get user events
    print("\n📊 Test 1: Getting user events for 'octocat'")
    try:
        events = await github_client.get_user_events("octocat", limit=5)
        print(f"✅ Found {len(events)} events for octocat")
        
        if events:
            print("📋 Recent events:")
            for event in events[:3]:  # Show first 3 events
                print(f"  - {event.type} on {event.repo.name if event.repo else 'unknown'} at {event.created_at}")
    except Exception as e:
        print(f"❌ Error getting user events: {e}")
    
    # Test 2: Get repository events
    print("\n📊 Test 2: Getting repository events for 'microsoft/vscode'")
    try:
        events = await github_client.get_repository_events("microsoft", "vscode", limit=5)
        print(f"✅ Found {len(events)} events for microsoft/vscode")
        
        if events:
            print("📋 Recent events:")
            for event in events[:3]:  # Show first 3 events
                actor = event.actor.login if event.actor else "unknown"
                print(f"  - {event.type} by {actor} at {event.created_at}")
    except Exception as e:
        print(f"❌ Error getting repository events: {e}")
    
    # Test 3: Get user activity
    print("\n📊 Test 3: Getting user activity for 'octocat'")
    try:
        activity = await github_client.get_user_activity("octocat", days=7)
        print(f"✅ Got activity summary for octocat")
        
        summary = activity.get("summary", {})
        print(f"📈 Activity summary:")
        print(f"  - Total events: {summary.get('total_events', 0)}")
        print(f"  - Active repositories: {len(summary.get('repositories_active', []))}")
        print(f"  - Event types: {summary.get('event_types', {})}")
        
    except Exception as e:
        print(f"❌ Error getting user activity: {e}")
    
    # Test 4: Get user commits
    print("\n📊 Test 4: Getting user commits for 'octocat'")
    try:
        commits = await github_client.get_user_commits("octocat", limit=5)
        print(f"✅ Found {len(commits)} commits for octocat")
        
        if commits:
            print("📋 Recent commits:")
            for commit in commits[:3]:  # Show first 3 commits
                message = commit.commit.message.split('\n')[0]  # First line only
                print(f"  - {commit.sha[:8]}: {message}")
    except Exception as e:
        print(f"❌ Error getting user commits: {e}")
    
    # Close the client
    await github_client.close()
    
    print("\n🎉 Example completed!")
    print("\nNext steps:")
    print("1. Run the MCP server: poetry run python -m mcp_github_actions")
    print("2. Connect it to your MCP client (like Claude Desktop)")
    print("3. Use the tools to fetch GitHub data")

if __name__ == "__main__":
    print("🐙 GitHub Actions MCP Server - Example Usage")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("src/mcp_github_actions"):
        print("❌ Please run this script from the project root directory")
        exit(1)
    
    asyncio.run(main()) 