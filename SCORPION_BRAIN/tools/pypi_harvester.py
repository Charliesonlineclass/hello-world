"""
SCORPION_BRAIN PyPI Harvester
=============================
Scrape and harvest data from PyPI packages.

Features:
- Package metadata retrieval
- Documentation extraction
- Dependency analysis
- Version history
"""

import json
import re
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PackageInfo:
    """Information about a PyPI package."""
    name: str
    version: str
    summary: str
    description: str
    author: str
    author_email: str
    license: str
    home_page: str
    project_urls: Dict[str, str]
    keywords: List[str]
    classifiers: List[str]
    requires_python: str


@dataclass
class PackageVersion:
    """A specific version of a package."""
    version: str
    release_date: datetime
    python_requires: str
    size: int
    downloads: int


@dataclass
class PackageDependency:
    """A package dependency."""
    name: str
    version_spec: str
    extras: List[str]
    is_optional: bool


@dataclass
class HarvestResult:
    """Result from harvesting a package."""
    package: PackageInfo
    versions: List[PackageVersion]
    dependencies: List[PackageDependency]
    readme: Optional[str]
    harvested_at: datetime


# Approved domains
APPROVED_DOMAINS = ["pypi.org", "pypi.python.org", "files.pythonhosted.org"]


class PyPIHarvester:
    """
    Harvest data from PyPI packages.

    Usage:
        harvester = PyPIHarvester()
        result = harvester.harvest("requests")
        deps = harvester.get_dependencies("flask")
    """

    def __init__(self, cache_dir: str = "/tmp/pypi_harvest"):
        self.base_url = "https://pypi.org/pypi"
        self.cache: Dict[str, Any] = {}

    def _make_request(self, url: str) -> Dict:
        """Make a request to PyPI API."""
        try:
            headers = {
                "Accept": "application/json",
                "User-Agent": "SCORPION_BRAIN-Harvester"
            }

            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode('utf-8'))

        except urllib.error.HTTPError as e:
            logger.error(f"HTTP error {e.code} for {url}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise

    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """
        Get package information.

        Args:
            package_name: PyPI package name

        Returns:
            PackageInfo or None
        """
        try:
            url = f"{self.base_url}/{package_name}/json"
            data = self._make_request(url)

            info = data.get("info", {})

            # Parse project URLs
            project_urls = info.get("project_urls") or {}
            if isinstance(project_urls, str):
                project_urls = {}

            return PackageInfo(
                name=info.get("name", package_name),
                version=info.get("version", ""),
                summary=info.get("summary", ""),
                description=info.get("description", ""),
                author=info.get("author", ""),
                author_email=info.get("author_email", ""),
                license=info.get("license", ""),
                home_page=info.get("home_page", ""),
                project_urls=project_urls,
                keywords=_parse_keywords(info.get("keywords", "")),
                classifiers=info.get("classifiers", []),
                requires_python=info.get("requires_python", "")
            )

        except Exception as e:
            logger.error(f"Failed to get package info: {e}")
            return None

    def get_versions(self, package_name: str, limit: int = 10) -> List[PackageVersion]:
        """
        Get package version history.

        Args:
            package_name: PyPI package name
            limit: Maximum versions to return

        Returns:
            List of PackageVersion
        """
        try:
            url = f"{self.base_url}/{package_name}/json"
            data = self._make_request(url)

            releases = data.get("releases", {})
            versions = []

            for version, release_info in releases.items():
                if not release_info:
                    continue

                # Get first release file info
                first_release = release_info[0]

                # Parse upload time
                upload_time = first_release.get("upload_time", "")
                if upload_time:
                    try:
                        release_date = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                    except ValueError:
                        release_date = datetime.now()
                else:
                    release_date = datetime.now()

                versions.append(PackageVersion(
                    version=version,
                    release_date=release_date,
                    python_requires=first_release.get("requires_python", ""),
                    size=first_release.get("size", 0),
                    downloads=0  # PyPI doesn't provide this directly
                ))

            # Sort by version (newest first) and limit
            versions.sort(key=lambda v: v.release_date, reverse=True)
            return versions[:limit]

        except Exception as e:
            logger.error(f"Failed to get versions: {e}")
            return []

    def get_dependencies(self, package_name: str) -> List[PackageDependency]:
        """
        Get package dependencies.

        Args:
            package_name: PyPI package name

        Returns:
            List of PackageDependency
        """
        try:
            url = f"{self.base_url}/{package_name}/json"
            data = self._make_request(url)

            info = data.get("info", {})
            requires = info.get("requires_dist") or []

            dependencies = []
            for req in requires:
                dep = _parse_requirement(req)
                if dep:
                    dependencies.append(dep)

            return dependencies

        except Exception as e:
            logger.error(f"Failed to get dependencies: {e}")
            return []

    def get_readme(self, package_name: str) -> Optional[str]:
        """
        Get package README/description.

        Args:
            package_name: PyPI package name

        Returns:
            Description content or None
        """
        try:
            info = self.get_package_info(package_name)
            if info:
                return info.description
            return None

        except Exception as e:
            logger.error(f"Failed to get README: {e}")
            return None

    def harvest(self, package_name: str) -> Optional[HarvestResult]:
        """
        Harvest complete package data.

        Args:
            package_name: PyPI package name

        Returns:
            HarvestResult or None
        """
        try:
            # Get package info
            info = self.get_package_info(package_name)
            if not info:
                return None

            # Get versions
            versions = self.get_versions(package_name)

            # Get dependencies
            dependencies = self.get_dependencies(package_name)

            return HarvestResult(
                package=info,
                versions=versions,
                dependencies=dependencies,
                readme=info.description,
                harvested_at=datetime.now()
            )

        except Exception as e:
            logger.error(f"Harvest failed: {e}")
            return None

    def search_packages(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for packages.

        Note: PyPI's search API is limited. This uses a simple approach.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of package info dicts
        """
        # PyPI doesn't have a great search API
        # We'll try the package directly first
        results = []

        # Try exact match
        info = self.get_package_info(query)
        if info:
            results.append({
                "name": info.name,
                "version": info.version,
                "summary": info.summary
            })

        # Try variations
        variations = [
            query.lower(),
            query.replace("-", "_"),
            query.replace("_", "-"),
            f"py{query}",
            f"python-{query}",
        ]

        for variation in variations:
            if len(results) >= limit:
                break
            if variation != query:
                info = self.get_package_info(variation)
                if info and info.name not in [r["name"] for r in results]:
                    results.append({
                        "name": info.name,
                        "version": info.version,
                        "summary": info.summary
                    })

        return results[:limit]

    def get_download_stats(self, package_name: str) -> Dict:
        """
        Get download statistics (from pypistats).

        Args:
            package_name: PyPI package name

        Returns:
            Dict with download stats
        """
        try:
            # Use pypistats API
            url = f"https://pypistats.org/api/packages/{package_name}/recent"
            headers = {"User-Agent": "SCORPION_BRAIN-Harvester"}

            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))

            return {
                "last_day": data.get("data", {}).get("last_day", 0),
                "last_week": data.get("data", {}).get("last_week", 0),
                "last_month": data.get("data", {}).get("last_month", 0)
            }

        except Exception as e:
            logger.debug(f"Failed to get download stats: {e}")
            return {"last_day": 0, "last_week": 0, "last_month": 0}


# Helper functions

def _parse_keywords(keywords: str) -> List[str]:
    """Parse keywords string into list."""
    if not keywords:
        return []
    if isinstance(keywords, list):
        return keywords
    return [k.strip() for k in keywords.split(",") if k.strip()]


def _parse_requirement(req: str) -> Optional[PackageDependency]:
    """Parse a requirement string into PackageDependency."""
    try:
        # Pattern: package_name[extras] (version_spec); condition
        match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[([^\]]+)\])?\s*(.*?)(?:;(.*))?$', req.strip())

        if not match:
            return None

        name = match.group(1)
        extras = match.group(2).split(",") if match.group(2) else []
        version_spec = match.group(3).strip() if match.group(3) else ""
        condition = match.group(4).strip() if match.group(4) else ""

        # Check if it's optional (has extra condition)
        is_optional = "extra" in condition.lower() if condition else False

        return PackageDependency(
            name=name,
            version_spec=version_spec,
            extras=extras,
            is_optional=is_optional
        )

    except Exception:
        return None


def harvest_package(package_name: str) -> Optional[HarvestResult]:
    """
    Quick function to harvest a package.

    Args:
        package_name: PyPI package name

    Returns:
        HarvestResult or None
    """
    harvester = PyPIHarvester()
    return harvester.harvest(package_name)


if __name__ == "__main__":
    # Demo
    harvester = PyPIHarvester()

    print("=== Package Info ===")
    info = harvester.get_package_info("requests")
    if info:
        print(f"Name: {info.name}")
        print(f"Version: {info.version}")
        print(f"Summary: {info.summary}")
        print(f"License: {info.license}")

    print("\n=== Dependencies ===")
    deps = harvester.get_dependencies("flask")
    for dep in deps[:5]:
        print(f"  - {dep.name} {dep.version_spec}")

    print("\n=== Versions ===")
    versions = harvester.get_versions("numpy", limit=5)
    for v in versions:
        print(f"  - {v.version} ({v.release_date.strftime('%Y-%m-%d')})")
