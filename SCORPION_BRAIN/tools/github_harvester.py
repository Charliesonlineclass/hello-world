"""
SCORPION_BRAIN GitHub Harvester
===============================
Scrape and harvest data from GitHub repositories.

Features:
- Repository cloning
- README extraction
- Code file parsing
- Issue/PR harvesting
- Rate limit handling
"""

import subprocess
import json
import re
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class RepoInfo:
    """Information about a GitHub repository."""
    owner: str
    name: str
    full_name: str
    description: str
    language: str
    stars: int
    forks: int
    topics: List[str]
    default_branch: str
    url: str


@dataclass
class FileContent:
    """Content from a repository file."""
    path: str
    name: str
    content: str
    size: int
    language: str
    sha: str


@dataclass
class HarvestResult:
    """Result from harvesting a repository."""
    repo: RepoInfo
    files: List[FileContent]
    readme: Optional[str]
    structure: Dict
    harvested_at: datetime


# Approved domains for harvesting
APPROVED_DOMAINS = ["github.com", "raw.githubusercontent.com", "api.github.com"]


class GitHubHarvester:
    """
    Harvest data from GitHub repositories.

    Usage:
        harvester = GitHubHarvester()
        result = harvester.harvest("owner/repo")
        files = harvester.get_code_files("owner/repo", ["*.py", "*.js"])
    """

    def __init__(
        self,
        token: str = None,
        cache_dir: str = "/tmp/github_harvest",
        rate_limit_delay: float = 1.0
    ):
        self.token = token
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit_delay = rate_limit_delay
        self._last_request = 0

    def _make_request(self, url: str) -> Dict:
        """Make a rate-limited request to GitHub API."""
        # Rate limiting
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SCORPION_BRAIN-Harvester"
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                self._last_request = time.time()
                return json.loads(response.read().decode('utf-8'))

        except urllib.error.HTTPError as e:
            if e.code == 403:
                logger.warning("Rate limit exceeded, waiting...")
                time.sleep(60)
                return self._make_request(url)
            raise

    def get_repo_info(self, repo: str) -> Optional[RepoInfo]:
        """
        Get repository information.

        Args:
            repo: Repository in "owner/name" format

        Returns:
            RepoInfo or None
        """
        try:
            url = f"https://api.github.com/repos/{repo}"
            data = self._make_request(url)

            return RepoInfo(
                owner=data["owner"]["login"],
                name=data["name"],
                full_name=data["full_name"],
                description=data.get("description", ""),
                language=data.get("language", "Unknown"),
                stars=data.get("stargazers_count", 0),
                forks=data.get("forks_count", 0),
                topics=data.get("topics", []),
                default_branch=data.get("default_branch", "main"),
                url=data["html_url"]
            )

        except Exception as e:
            logger.error(f"Failed to get repo info: {e}")
            return None

    def get_readme(self, repo: str) -> Optional[str]:
        """
        Get repository README content.

        Args:
            repo: Repository in "owner/name" format

        Returns:
            README content or None
        """
        try:
            url = f"https://api.github.com/repos/{repo}/readme"
            data = self._make_request(url)

            # Decode content
            import base64
            content = base64.b64decode(data["content"]).decode('utf-8')
            return content

        except Exception as e:
            logger.error(f"Failed to get README: {e}")
            return None

    def get_tree(self, repo: str, branch: str = None) -> List[Dict]:
        """
        Get repository file tree.

        Args:
            repo: Repository in "owner/name" format
            branch: Branch name (defaults to default branch)

        Returns:
            List of file entries
        """
        try:
            if not branch:
                info = self.get_repo_info(repo)
                branch = info.default_branch if info else "main"

            url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
            data = self._make_request(url)

            return data.get("tree", [])

        except Exception as e:
            logger.error(f"Failed to get tree: {e}")
            return []

    def get_file_content(self, repo: str, path: str) -> Optional[FileContent]:
        """
        Get content of a specific file.

        Args:
            repo: Repository in "owner/name" format
            path: File path in repository

        Returns:
            FileContent or None
        """
        try:
            url = f"https://api.github.com/repos/{repo}/contents/{path}"
            data = self._make_request(url)

            if data.get("type") != "file":
                return None

            # Decode content
            import base64
            content = base64.b64decode(data["content"]).decode('utf-8', errors='ignore')

            # Determine language from extension
            ext = Path(path).suffix.lower()
            language = _ext_to_language(ext)

            return FileContent(
                path=path,
                name=data["name"],
                content=content,
                size=data.get("size", len(content)),
                language=language,
                sha=data.get("sha", "")
            )

        except Exception as e:
            logger.error(f"Failed to get file: {e}")
            return None

    def get_code_files(
        self,
        repo: str,
        patterns: List[str] = None,
        max_files: int = 50
    ) -> List[FileContent]:
        """
        Get code files matching patterns.

        Args:
            repo: Repository in "owner/name" format
            patterns: File patterns (e.g., ["*.py", "*.js"])
            max_files: Maximum files to retrieve

        Returns:
            List of FileContent
        """
        patterns = patterns or ["*.py", "*.js", "*.ts", "*.go", "*.rs"]

        # Get file tree
        tree = self.get_tree(repo)

        # Filter files
        matching_files = []
        for item in tree:
            if item["type"] != "blob":
                continue

            path = item["path"]
            for pattern in patterns:
                if _match_pattern(path, pattern):
                    matching_files.append(path)
                    break

        # Limit files
        matching_files = matching_files[:max_files]

        # Fetch content
        files = []
        for path in matching_files:
            content = self.get_file_content(repo, path)
            if content:
                files.append(content)
                time.sleep(0.5)  # Rate limit

        return files

    def harvest(self, repo: str, include_code: bool = True) -> Optional[HarvestResult]:
        """
        Harvest complete repository data.

        Args:
            repo: Repository in "owner/name" format
            include_code: Whether to include code files

        Returns:
            HarvestResult or None
        """
        try:
            # Get repo info
            info = self.get_repo_info(repo)
            if not info:
                return None

            # Get README
            readme = self.get_readme(repo)

            # Get file structure
            tree = self.get_tree(repo)
            structure = _build_structure(tree)

            # Get code files
            files = []
            if include_code:
                files = self.get_code_files(repo, max_files=30)

            return HarvestResult(
                repo=info,
                files=files,
                readme=readme,
                structure=structure,
                harvested_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Harvest failed: {e}")
            return None

    def clone_repo(self, repo: str, target_dir: str = None) -> Optional[str]:
        """
        Clone a repository locally.

        Args:
            repo: Repository in "owner/name" format
            target_dir: Directory to clone into

        Returns:
            Path to cloned repo or None
        """
        if target_dir is None:
            target_dir = str(self.cache_dir / repo.replace("/", "_"))

        try:
            if Path(target_dir).exists():
                # Pull latest
                subprocess.run(
                    ["git", "-C", target_dir, "pull"],
                    capture_output=True,
                    timeout=120
                )
            else:
                # Clone
                subprocess.run(
                    ["git", "clone", f"https://github.com/{repo}.git", target_dir],
                    capture_output=True,
                    timeout=300
                )

            return target_dir

        except Exception as e:
            logger.error(f"Clone failed: {e}")
            return None

    def search_repos(self, query: str, limit: int = 10) -> List[RepoInfo]:
        """
        Search for repositories.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of RepoInfo
        """
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.github.com/search/repositories?q={encoded_query}&per_page={limit}"
            data = self._make_request(url)

            repos = []
            for item in data.get("items", [])[:limit]:
                repos.append(RepoInfo(
                    owner=item["owner"]["login"],
                    name=item["name"],
                    full_name=item["full_name"],
                    description=item.get("description", ""),
                    language=item.get("language", "Unknown"),
                    stars=item.get("stargazers_count", 0),
                    forks=item.get("forks_count", 0),
                    topics=item.get("topics", []),
                    default_branch=item.get("default_branch", "main"),
                    url=item["html_url"]
                ))

            return repos

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


# Helper functions

def _ext_to_language(ext: str) -> str:
    """Map file extension to language."""
    mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".go": "Go",
        ".rs": "Rust",
        ".java": "Java",
        ".rb": "Ruby",
        ".php": "PHP",
        ".c": "C",
        ".cpp": "C++",
        ".h": "C/C++ Header",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".md": "Markdown",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".xml": "XML",
        ".html": "HTML",
        ".css": "CSS",
        ".sh": "Shell",
        ".bash": "Bash",
    }
    return mapping.get(ext, "Unknown")


def _match_pattern(path: str, pattern: str) -> bool:
    """Match file path against glob pattern."""
    import fnmatch
    return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern)


def _build_structure(tree: List[Dict]) -> Dict:
    """Build a directory structure from file tree."""
    structure = {"dirs": {}, "files": []}

    for item in tree:
        parts = item["path"].split("/")

        if item["type"] == "blob":
            # It's a file
            if len(parts) == 1:
                structure["files"].append(parts[0])
            else:
                # Navigate to parent dir
                current = structure
                for part in parts[:-1]:
                    if part not in current["dirs"]:
                        current["dirs"][part] = {"dirs": {}, "files": []}
                    current = current["dirs"][part]
                current["files"].append(parts[-1])

    return structure


def harvest_repo(repo: str, token: str = None) -> Optional[HarvestResult]:
    """
    Quick function to harvest a repository.

    Args:
        repo: Repository in "owner/name" format
        token: Optional GitHub token

    Returns:
        HarvestResult or None
    """
    harvester = GitHubHarvester(token=token)
    return harvester.harvest(repo)


# Need to import urllib.parse for URL encoding
import urllib.parse


if __name__ == "__main__":
    # Demo
    harvester = GitHubHarvester()

    print("=== Repository Info ===")
    info = harvester.get_repo_info("python/cpython")
    if info:
        print(f"Name: {info.full_name}")
        print(f"Language: {info.language}")
        print(f"Stars: {info.stars}")
        print(f"Topics: {info.topics[:5]}")

    print("\n=== Search ===")
    repos = harvester.search_repos("machine learning python", limit=3)
    for repo in repos:
        print(f"  - {repo.full_name} ({repo.stars} stars)")
