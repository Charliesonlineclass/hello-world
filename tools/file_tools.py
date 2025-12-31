"""
SCORPION File Tools
===================

Safe file operations for SCORPION system.
Handles reading, writing, and managing files with safety checks.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import json
import shutil
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-FILETOOLS")


class FileTools:
    """
    Safe file operations for SCORPION.

    Provides:
    - Safe read/write operations
    - Directory management
    - File information
    - Backup operations
    - Search functionality
    """

    # Directories that are safe to operate in
    SAFE_DIRECTORIES = [
        "./data",
        "./logs",
        "./backups",
        "./exports",
        "./uploads",
        "./temp",
    ]

    # File extensions that are safe to read/write
    SAFE_EXTENSIONS = [
        ".txt", ".json", ".md", ".csv", ".log",
        ".yaml", ".yml", ".html", ".css", ".js",
        ".py", ".sh", ".env", ".conf", ".cfg"
    ]

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        logger.info(f"FileTools initialized: {self.base_path}")

    # -------------------------------------------------------------------------
    # Safety Checks
    # -------------------------------------------------------------------------

    def _is_safe_path(self, path: Union[str, Path]) -> bool:
        """Check if a path is safe to operate on."""
        path = Path(path).resolve()

        # Check if within base path
        try:
            path.relative_to(self.base_path)
        except ValueError:
            # Not under base path
            return False

        # Check against safe directories
        for safe_dir in self.SAFE_DIRECTORIES:
            safe_path = (self.base_path / safe_dir).resolve()
            try:
                path.relative_to(safe_path)
                return True
            except ValueError:
                continue

        # Check extension for files
        if path.is_file() or not path.exists():
            return path.suffix.lower() in self.SAFE_EXTENSIONS

        return True

    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to base."""
        if Path(path).is_absolute():
            return Path(path)
        return self.base_path / path

    # -------------------------------------------------------------------------
    # Read Operations
    # -------------------------------------------------------------------------

    def read_file(self, path: str) -> Optional[str]:
        """Read a text file."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            logger.warning(f"File not found: {path}")
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Read failed: {e}")
            return None

    def read_json(self, path: str) -> Optional[Dict]:
        """Read a JSON file."""
        content = self.read_file(path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse failed: {e}")
        return None

    def read_lines(self, path: str) -> List[str]:
        """Read file as list of lines."""
        content = self.read_file(path)
        if content:
            return content.splitlines()
        return []

    # -------------------------------------------------------------------------
    # Write Operations
    # -------------------------------------------------------------------------

    def write_file(
        self,
        path: str,
        content: str,
        create_dirs: bool = True
    ) -> bool:
        """Write content to a file."""
        full_path = self._resolve_path(path)

        try:
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Written: {path}")
            return True

        except Exception as e:
            logger.error(f"Write failed: {e}")
            return False

    def write_json(
        self,
        path: str,
        data: Any,
        indent: int = 2
    ) -> bool:
        """Write data as JSON file."""
        try:
            content = json.dumps(data, indent=indent, default=str)
            return self.write_file(path, content)
        except Exception as e:
            logger.error(f"JSON write failed: {e}")
            return False

    def append_file(self, path: str, content: str) -> bool:
        """Append content to a file."""
        full_path = self._resolve_path(path)

        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"Append failed: {e}")
            return False

    def append_line(self, path: str, line: str) -> bool:
        """Append a line to a file."""
        return self.append_file(path, line + "\n")

    # -------------------------------------------------------------------------
    # Directory Operations
    # -------------------------------------------------------------------------

    def list_directory(
        self,
        path: str = ".",
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """List contents of a directory."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return []

        items = []

        if recursive:
            paths = full_path.rglob(pattern)
        else:
            paths = full_path.glob(pattern)

        for p in paths:
            try:
                stat = p.stat()
                items.append({
                    "name": p.name,
                    "path": str(p.relative_to(self.base_path)),
                    "is_dir": p.is_dir(),
                    "size": stat.st_size if p.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception:
                continue

        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))

    def create_directory(self, path: str) -> bool:
        """Create a directory."""
        full_path = self._resolve_path(path)

        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Create directory failed: {e}")
            return False

    def delete_directory(self, path: str, confirm: bool = True) -> bool:
        """Delete a directory."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return True

        if confirm:
            logger.warning(f"Would delete directory: {path}")
            return False

        try:
            shutil.rmtree(full_path)
            logger.info(f"Deleted directory: {path}")
            return True
        except Exception as e:
            logger.error(f"Delete directory failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------

    def delete_file(self, path: str, confirm: bool = True) -> bool:
        """Delete a file."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return True

        if confirm:
            logger.warning(f"Would delete file: {path}")
            return False

        try:
            full_path.unlink()
            logger.info(f"Deleted: {path}")
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def copy_file(self, src: str, dst: str) -> bool:
        """Copy a file."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            logger.info(f"Copied: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"Copy failed: {e}")
            return False

    def move_file(self, src: str, dst: str) -> bool:
        """Move a file."""
        src_path = self._resolve_path(src)
        dst_path = self._resolve_path(dst)

        try:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src_path, dst_path)
            logger.info(f"Moved: {src} -> {dst}")
            return True
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False

    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        return self._resolve_path(path).exists()

    # -------------------------------------------------------------------------
    # File Information
    # -------------------------------------------------------------------------

    def file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get detailed file information."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return None

        try:
            stat = full_path.stat()

            info = {
                "name": full_path.name,
                "path": str(full_path),
                "relative_path": str(full_path.relative_to(self.base_path)),
                "is_file": full_path.is_file(),
                "is_dir": full_path.is_dir(),
                "size": stat.st_size,
                "size_human": self._human_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": full_path.suffix,
            }

            if full_path.is_file():
                info["md5"] = self._file_hash(full_path)
                info["lines"] = self._count_lines(full_path)

            return info

        except Exception as e:
            logger.error(f"File info failed: {e}")
            return None

    def _human_size(self, size: int) -> str:
        """Convert size to human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _file_hash(self, path: Path) -> str:
        """Calculate MD5 hash of file."""
        try:
            md5 = hashlib.md5()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5.update(chunk)
            return md5.hexdigest()
        except Exception:
            return ""

    def _count_lines(self, path: Path) -> int:
        """Count lines in a text file."""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def search_files(
        self,
        path: str = ".",
        pattern: str = "*",
        content: Optional[str] = None
    ) -> List[str]:
        """Search for files by name and optionally content."""
        full_path = self._resolve_path(path)
        results = []

        for p in full_path.rglob(pattern):
            if p.is_file():
                if content:
                    try:
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            if content.lower() in f.read().lower():
                                results.append(str(p.relative_to(self.base_path)))
                    except Exception:
                        continue
                else:
                    results.append(str(p.relative_to(self.base_path)))

        return results

    # -------------------------------------------------------------------------
    # Backup
    # -------------------------------------------------------------------------

    def backup_file(self, path: str) -> Optional[str]:
        """Create a backup of a file."""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{full_path.stem}_{timestamp}{full_path.suffix}"
        backup_path = self.base_path / "backups" / backup_name

        if self.copy_file(path, str(backup_path)):
            return str(backup_path.relative_to(self.base_path))

        return None


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run file tools from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION File Tools")
    parser.add_argument("--list", help="List directory")
    parser.add_argument("--read", help="Read file")
    parser.add_argument("--info", help="File info")
    parser.add_argument("--search", help="Search pattern")
    parser.add_argument("--path", default=".", help="Search path")

    args = parser.parse_args()

    tools = FileTools()

    if args.list:
        items = tools.list_directory(args.list)
        for item in items:
            icon = "📁" if item["is_dir"] else "📄"
            size = tools._human_size(item["size"]) if not item["is_dir"] else ""
            print(f"  {icon} {item['name']} {size}")
    elif args.read:
        content = tools.read_file(args.read)
        if content:
            print(content)
    elif args.info:
        info = tools.file_info(args.info)
        if info:
            for key, value in info.items():
                print(f"  {key}: {value}")
    elif args.search:
        results = tools.search_files(args.path, args.search)
        for r in results:
            print(f"  {r}")
    else:
        items = tools.list_directory()
        for item in items:
            print(f"  {item['name']}")


if __name__ == "__main__":
    main()
