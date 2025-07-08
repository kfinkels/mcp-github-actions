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

async def test_server_functions(username='kfinkels'):
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
    print(f"\n📊 Test 1: Get user events for '{username}'")
    try:
        result = await server._get_user_events(username, 5)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"📋 Found {len(data)} events")
        for event in data[:2]:  # Show first 2
            print(f"  - {event['type']} on {event['repo']} at {event['created_at']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Get user activity
    print(f"\n📊 Test 2: Get user activity for '{username}'")
    try:
        result = await server._get_user_activity(username, 7)
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
    
    # Test 3: Get repository events - Skip if no known repos
    print(f"\n📊 Test 3: Get user commits for '{username}'")
    try:
        result = await server._get_user_commits(username, None, 5)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"📋 Found {len(data)} commits")
        for commit in data[:2]:  # Show first 2
            message = commit['message'].split('\n')[0]  # First line only
            print(f"  - {commit['sha'][:8]}: {message}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get user tech stack
    print(f"\n📊 Test 4: Get tech stack analysis for '{username}'")
    try:
        result = await server._get_user_tech_stack(username, 365, 20)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"🔧 Tech Stack Analysis:")
        print(f"  - Commits analyzed: {data.get('analysis_period', {}).get('commits_analyzed', 0)}")
        print(f"  - Programming languages: {len(data.get('programming_languages', {}))}")
        if data.get('top_languages'):
            print(f"  - Top languages: {[lang['language'] for lang in data.get('top_languages', [])][:3]}")
        if data.get('top_frameworks'):
            print(f"  - Top frameworks: {[fw['name'] for fw in data.get('top_frameworks', [])][:3]}")
        if data.get('change_types'):
            print(f"  - Change types: {[ct['type'] for ct in data.get('change_types', [])][:3]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Generate work experience
    print(f"\n📊 Test 5: Generate work experience profile for '{username}'")
    try:
        result = await server._generate_work_experience(username, None, None, 365)
        print("✅ Success!")
        data = json.loads(result[0].text)
        print(f"💼 Work Experience Profile:")
        print(f"  - Role: {data.get('role_title_inferred', 'N/A')}")
        print(f"  - Organization: {data.get('organization', 'N/A')}")
        print(f"  - Period: {data.get('start_date', 'N/A')} to {data.get('end_date', 'N/A')}")
        print(f"  - Technologies: {', '.join(data.get('technologies', [])[:5])}")
        print(f"  - Methodologies: {', '.join(data.get('methodologies', []))}")
        print(f"  - Total commits: {data.get('metrics', {}).get('total_commits', 0)}")
        print(f"  - Key achievements:")
        for achievement in data.get('key_achievements', [])[:2]:
            print(f"    • {achievement}")
        print(f"  - LinkedIn summary: {data.get('summary_for_linkedin', 'N/A')[:150]}...")
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
    print("5. get_user_tech_stack <username> [days] [limit]")
    print("6. generate_work_experience <username> [repo_name] [organization] [days]")
    print("7. quit")
    
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
            
            elif cmd == 'get_user_tech_stack':
                username = args[0]
                days = int(args[1]) if len(args) > 1 else 365
                limit = int(args[2]) if len(args) > 2 else 50
                result = await server._get_user_tech_stack(username, days, limit)
                data = json.loads(result[0].text)
                print(f"🔧 Tech Stack Analysis for {username} (last {days} days):")
                print(f"  - Commits analyzed: {data.get('analysis_period', {}).get('commits_analyzed', 0)}")
                print(f"  - Repositories: {len(data.get('commit_summary', {}).get('repos_contributed', []))}")
                
                if data.get('top_languages'):
                    print(f"  - Top languages:")
                    for lang in data['top_languages'][:3]:
                        print(f"    • {lang['language']}: {lang['files']} files ({lang['percentage']}%)")
                
                if data.get('top_frameworks'):
                    print(f"  - Top frameworks:")
                    for fw in data['top_frameworks'][:3]:
                        print(f"    • {fw['name']}: {fw['mentions']} mentions")
                
                if data.get('top_tools'):
                    print(f"  - Top tools:")
                    for tool in data['top_tools'][:3]:
                        print(f"    • {tool['name']}: {tool['mentions']} mentions")
                
                if data.get('change_types'):
                    print(f"  - Change types:")
                    for ct in data['change_types'][:3]:
                        print(f"    • {ct['type']}: {ct['count']} commits ({ct['percentage']}%)")
            
            elif cmd == 'generate_work_experience':
                username = args[0]
                repo_name = args[1] if len(args) > 1 else None
                organization = args[2] if len(args) > 2 else None
                days = int(args[3]) if len(args) > 3 else 365
                result = await server._generate_work_experience(username, repo_name, organization, days)
                data = json.loads(result[0].text)
                print(f"💼 Work Experience Profile for {username}:")
                print(f"  - Role: {data.get('role_title_inferred', 'N/A')}")
                print(f"  - Organization: {data.get('organization', 'N/A')}")
                print(f"  - Period: {data.get('start_date', 'N/A')} to {data.get('end_date', 'N/A')}")
                print(f"  - Technologies: {', '.join(data.get('technologies', [])[:5])}")
                print(f"  - Total commits: {data.get('metrics', {}).get('total_commits', 0)}")
                print(f"  - Key responsibilities:")
                for resp in data.get('responsibilities', [])[:3]:
                    print(f"    • {resp}")
                print(f"  - LinkedIn summary: {data.get('summary_for_linkedin', 'N/A')[:100]}...")
            
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
    elif len(sys.argv) > 1:
        # Use provided username
        username = sys.argv[1]
        asyncio.run(test_server_functions(username))
    else:
        asyncio.run(test_server_functions()) 