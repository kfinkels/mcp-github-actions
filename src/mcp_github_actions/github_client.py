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
                since_date = datetime.now().replace(tzinfo=None) - timedelta(days=365)  # Default to 1 year instead of 30 days
            
            commits = []
            repos = user.get_repos(type="owner", sort="updated")
            
            for repo in repos:
                # Remove the repo filtering based on update date - we want to check all repos for commits
                # The since_date should only apply to individual commits, not repo filtering
                
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
    
    async def get_user_tech_stack(self, username: str, days: int = 365, limit: int = 100) -> Dict[str, Any]:
        """Analyze user's commits to extract tech stack, programming languages, and change patterns."""
        try:
            user = self.github.get_user(username)
            since_date = datetime.now().replace(tzinfo=None) - timedelta(days=days)
            
            # Initialize analysis structure
            analysis = {
                "user": username,
                "analysis_period": {
                    "days": days,
                    "since": since_date.isoformat(),
                    "commits_analyzed": 0
                },
                "programming_languages": {},
                "tech_stack": {
                    "frameworks": {},
                    "libraries": {},
                    "tools": {},
                    "databases": {},
                    "cloud_services": {}
                },
                "file_types": {},
                "change_patterns": {
                    "additions": 0,
                    "deletions": 0,
                    "modifications": 0,
                    "new_files": 0,
                    "deleted_files": 0
                },
                "commit_summary": {
                    "total_commits": 0,
                    "repos_contributed": set(),
                    "change_descriptions": []
                }
            }
            
            # Get user's repositories
            repos = user.get_repos(type="all", sort="updated")
            commits_analyzed = 0
            
            for repo in repos:
                if commits_analyzed >= limit:
                    break
                
                # Remove repo filtering based on update date - check all repos for user's commits
                # The since_date should only apply to individual commits, not repo filtering
                
                try:
                    # Get commits from this repository
                    commits = repo.get_commits(author=username, since=since_date)
                    
                    # Convert PaginatedList to list safely
                    commit_list = []
                    try:
                        for commit in commits:
                            if len(commit_list) >= limit - commits_analyzed:
                                break
                            commit_list.append(commit)
                    except Exception as e:
                        logger.warning(f"Error iterating commits for {repo.full_name}: {e}")
                        continue
                    
                    for commit in commit_list:
                        if commits_analyzed >= limit:
                            break
                            
                        analysis["commit_summary"]["total_commits"] += 1
                        analysis["commit_summary"]["repos_contributed"].add(repo.full_name)
                        
                        # Analyze commit message for change description
                        commit_msg = commit.commit.message.lower()
                        change_desc = self._categorize_commit_message(commit_msg)
                        if change_desc:
                            analysis["commit_summary"]["change_descriptions"].append(change_desc)
                        
                        # Analyze files changed in this commit
                        try:
                            files = commit.files
                            if files:  # Check if files exist
                                for file in files:
                                    # Count file operations
                                    if file.status == "added":
                                        analysis["change_patterns"]["new_files"] += 1
                                    elif file.status == "removed":
                                        analysis["change_patterns"]["deleted_files"] += 1
                                    elif file.status == "modified":
                                        analysis["change_patterns"]["modifications"] += 1
                                    
                                    # Track additions/deletions
                                    analysis["change_patterns"]["additions"] += file.additions
                                    analysis["change_patterns"]["deletions"] += file.deletions
                                    
                                    # Analyze file extension for programming language
                                    filename = file.filename
                                    self._analyze_file_extension(filename, analysis)
                                    
                                    # Analyze file content for tech stack
                                    if file.patch:
                                        self._analyze_file_content(file.patch, filename, analysis)
                        
                        except Exception as e:
                            logger.warning(f"Error analyzing commit {commit.sha}: {e}")
                        
                        commits_analyzed += 1
                        
                except Exception as e:
                    logger.warning(f"Error getting commits for {repo.full_name}: {e}")
            
            # Convert sets to lists for JSON serialization
            analysis["commit_summary"]["repos_contributed"] = list(analysis["commit_summary"]["repos_contributed"])
            analysis["analysis_period"]["commits_analyzed"] = commits_analyzed
            
            # Calculate percentages and top items
            analysis = self._calculate_tech_stack_stats(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing tech stack for {username}: {e}")
            raise
    
    def _analyze_file_extension(self, filename: str, analysis: Dict[str, Any]) -> None:
        """Analyze file extension to determine programming language."""
        # Language mapping
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript/React',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript/React',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.r': 'R',
            '.R': 'R',
            '.sql': 'SQL',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.vue': 'Vue.js',
            '.svelte': 'Svelte',
            '.dart': 'Dart',
            '.lua': 'Lua',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.fish': 'Fish',
            '.ps1': 'PowerShell',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.cfg': 'Config',
            '.md': 'Markdown',
            '.dockerfile': 'Docker',
            '.tf': 'Terraform',
            '.hcl': 'HCL'
        }
        
        # Get file extension
        if '.' in filename:
            ext = '.' + filename.split('.')[-1].lower()
            if ext in language_map:
                lang = language_map[ext]
                analysis["programming_languages"][lang] = analysis["programming_languages"].get(lang, 0) + 1
        
        # Track file types
        file_type = filename.split('.')[-1].lower() if '.' in filename else 'no_extension'
        analysis["file_types"][file_type] = analysis["file_types"].get(file_type, 0) + 1
    
    def _analyze_file_content(self, patch: str, filename: str, analysis: Dict[str, Any]) -> None:
        """Analyze file content to identify tech stack."""
        if not patch:
            return
        
        patch_lower = patch.lower()
        
        # Tech stack patterns
        tech_patterns = {
            'frameworks': {
                'react': ['react', 'jsx', 'usestate', 'useeffect', 'component'],
                'angular': ['angular', '@angular', 'ngmodule', 'component'],
                'vue': ['vue', 'vuex', 'vue-router'],
                'django': ['django', 'from django', 'models.model'],
                'flask': ['flask', 'from flask', 'app = flask'],
                'express': ['express', 'app.get', 'app.post', 'req.body'],
                'fastapi': ['fastapi', 'from fastapi', '@app.get'],
                'spring': ['spring', '@controller', '@service', '@repository'],
                'rails': ['rails', 'activerecord', 'controller'],
                'laravel': ['laravel', 'eloquent', 'artisan'],
                'nextjs': ['next', 'getserversideprops', 'getstatic'],
                'nuxt': ['nuxt', 'asyncdata', 'nuxtjs'],
                'svelte': ['svelte', 'svelte/store'],
                'flutter': ['flutter', 'widget', 'statefulwidget'],
                'tensorflow': ['tensorflow', 'keras', 'tf.'],
                'pytorch': ['torch', 'pytorch', 'nn.module'],
                'scikit-learn': ['sklearn', 'scikit-learn', 'fit()', 'predict()']
            },
            'libraries': {
                'axios': ['axios', 'axios.get', 'axios.post'],
                'lodash': ['lodash', '_.map', '_.filter'],
                'moment': ['moment', 'moment()'],
                'jquery': ['jquery', '$(' , '$.ajax'],
                'numpy': ['numpy', 'np.array', 'import numpy'],
                'pandas': ['pandas', 'pd.dataframe', 'import pandas'],
                'matplotlib': ['matplotlib', 'pyplot', 'plt.plot'],
                'requests': ['requests', 'requests.get', 'requests.post'],
                'beautifulsoup': ['beautifulsoup', 'bs4', 'soup.find'],
                'selenium': ['selenium', 'webdriver', 'driver.find'],
                'pytest': ['pytest', 'def test_', 'assert'],
                'jest': ['jest', 'test(', 'expect('],
                'mocha': ['mocha', 'describe(', 'it('],
                'cypress': ['cypress', 'cy.visit', 'cy.get'],
                'bootstrap': ['bootstrap', 'btn-primary', 'container'],
                'tailwind': ['tailwind', 'bg-blue', 'text-center'],
                'material-ui': ['material-ui', 'mui', '@mui/'],
                'styled-components': ['styled-components', 'styled.div']
            },
            'tools': {
                'webpack': ['webpack', 'webpack.config', 'module.exports'],
                'vite': ['vite', 'vite.config', 'import.meta'],
                'babel': ['babel', '.babelrc', 'babel.config'],
                'eslint': ['eslint', '.eslintrc', 'eslint-disable'],
                'prettier': ['prettier', '.prettierrc', 'prettier-ignore'],
                'typescript': ['typescript', 'interface', 'type '],
                'jest': ['jest', 'jest.config', 'setupTests'],
                'docker': ['docker', 'dockerfile', 'docker-compose'],
                'git': ['git', '.gitignore', 'git add'],
                'npm': ['package.json', 'npm install', 'npm run'],
                'yarn': ['yarn', 'yarn.lock', 'yarn add'],
                'poetry': ['poetry', 'pyproject.toml', 'poetry add'],
                'pip': ['requirements.txt', 'pip install', 'pip freeze'],
                'gradle': ['gradle', 'build.gradle', 'gradlew'],
                'maven': ['maven', 'pom.xml', 'mvn'],
                'makefile': ['makefile', 'make', 'gcc']
            },
            'databases': {
                'postgresql': ['postgresql', 'psycopg2', 'pg_dump'],
                'mysql': ['mysql', 'mysqldump', 'pymysql'],
                'mongodb': ['mongodb', 'mongoose', 'pymongo'],
                'redis': ['redis', 'redis.get', 'redis.set'],
                'sqlite': ['sqlite', 'sqlite3', 'db.sqlite'],
                'elasticsearch': ['elasticsearch', 'es.search', 'elastic'],
                'cassandra': ['cassandra', 'cql', 'cassandra-driver'],
                'dynamodb': ['dynamodb', 'boto3', 'dynamodb.table']
            },
            'cloud_services': {
                'aws': ['aws', 'boto3', 's3.bucket', 'lambda', 'ec2'],
                'gcp': ['gcp', 'google-cloud', 'bigquery', 'datastore'],
                'azure': ['azure', 'azure-storage', 'azure-functions'],
                'heroku': ['heroku', 'procfile', 'heroku.yml'],
                'vercel': ['vercel', 'vercel.json', 'now.json'],
                'netlify': ['netlify', 'netlify.toml', '_redirects'],
                'firebase': ['firebase', 'firestore', 'firebase.json'],
                'cloudflare': ['cloudflare', 'workers', 'wrangler']
            }
        }
        
        # Search for patterns in the patch
        for category, techs in tech_patterns.items():
            for tech_name, patterns in techs.items():
                for pattern in patterns:
                    if pattern in patch_lower:
                        analysis["tech_stack"][category][tech_name] = analysis["tech_stack"][category].get(tech_name, 0) + 1
                        break  # Only count once per patch
    
    def _categorize_commit_message(self, message: str) -> str:
        """Categorize commit message to understand type of change."""
        message = message.lower()
        
        # Common commit patterns
        patterns = {
            'feature': ['feat', 'feature', 'add', 'implement', 'new'],
            'bugfix': ['fix', 'bug', 'issue', 'problem', 'error'],
            'refactor': ['refactor', 'refactoring', 'cleanup', 'restructure'],
            'documentation': ['docs', 'documentation', 'readme', 'comment'],
            'test': ['test', 'testing', 'spec', 'unit test'],
            'style': ['style', 'formatting', 'css', 'ui', 'design'],
            'performance': ['performance', 'optimize', 'speed', 'improve'],
            'security': ['security', 'vulnerability', 'auth', 'permission'],
            'dependency': ['dependency', 'package', 'upgrade', 'update'],
            'configuration': ['config', 'configuration', 'setting', 'env'],
            'deployment': ['deploy', 'deployment', 'release', 'build'],
            'database': ['database', 'migration', 'schema', 'sql'],
            'api': ['api', 'endpoint', 'route', 'service'],
            'ui': ['ui', 'frontend', 'interface', 'component']
        }
        
        for category, keywords in patterns.items():
            if any(keyword in message for keyword in keywords):
                return category
        
        return 'other'
    
    def _calculate_tech_stack_stats(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistics and top items for tech stack analysis."""
        
        # Calculate top programming languages
        if analysis["programming_languages"]:
            total_lang_files = sum(analysis["programming_languages"].values())
            analysis["top_languages"] = [
                {
                    "language": lang,
                    "files": count,
                    "percentage": round((count / total_lang_files) * 100, 1)
                }
                for lang, count in sorted(analysis["programming_languages"].items(), key=lambda x: x[1], reverse=True)
            ][:10]
        
        # Calculate top tech stack items
        for category in analysis["tech_stack"]:
            if analysis["tech_stack"][category]:
                analysis[f"top_{category}"] = [
                    {
                        "name": tech,
                        "mentions": count
                    }
                    for tech, count in sorted(analysis["tech_stack"][category].items(), key=lambda x: x[1], reverse=True)
                ][:5]
        
        # Categorize change descriptions
        if analysis["commit_summary"]["change_descriptions"]:
            change_counts = {}
            for desc in analysis["commit_summary"]["change_descriptions"]:
                change_counts[desc] = change_counts.get(desc, 0) + 1
            
            analysis["change_types"] = [
                {
                    "type": change_type,
                    "count": count,
                    "percentage": round((count / len(analysis["commit_summary"]["change_descriptions"])) * 100, 1)
                }
                for change_type, count in sorted(change_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        
        return analysis
    
    async def close(self):
        """Close the HTTP session."""
        await self.session.aclose() 