"""
GitHub Repository Cloner
Clones public GitHub repositories for analysis
"""
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse


class GitHubCloner:
    """
    Utility to clone GitHub repositories for analysis
    """

    def __init__(self, workspace_dir: Optional[str] = None):
        """
        Initialize GitHub cloner

        Args:
            workspace_dir: Directory to clone repos into. If None, uses temp directory.
        """
        if workspace_dir:
            self.workspace_dir = Path(workspace_dir)
            self.workspace_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.workspace_dir = Path(tempfile.gettempdir()) / "codebase_analysis"
            self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate_github_url(self, url: str) -> Dict[str, Any]:
        """
        Validate if URL is a valid GitHub repository URL

        Args:
            url: GitHub repository URL

        Returns:
            Dictionary with validation result and parsed info
        """
        try:
            parsed = urlparse(url)

            # Check if it's GitHub
            if parsed.netloc not in ['github.com', 'www.github.com']:
                return {
                    "valid": False,
                    "error": "Not a GitHub URL. Please provide a github.com URL."
                }

            # Extract owner and repo name
            path_parts = parsed.path.strip('/').split('/')

            if len(path_parts) < 2:
                return {
                    "valid": False,
                    "error": "Invalid GitHub URL format. Expected: https://github.com/owner/repo"
                }

            owner = path_parts[0]
            repo = path_parts[1].replace('.git', '')  # Remove .git if present

            return {
                "valid": True,
                "owner": owner,
                "repo": repo,
                "clone_url": f"https://github.com/{owner}/{repo}.git"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Error parsing URL: {str(e)}"
            }

    def clone_repository(self, github_url: str) -> Dict[str, Any]:
        """
        Clone a GitHub repository

        Args:
            github_url: GitHub repository URL

        Returns:
            Dictionary with clone result and local path
        """
        # Validate URL
        validation = self.validate_github_url(github_url)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"]
            }

        owner = validation["owner"]
        repo = validation["repo"]
        clone_url = validation["clone_url"]

        # Create directory for this repo
        repo_dir = self.workspace_dir / f"{owner}_{repo}"

        # Remove if already exists
        if repo_dir.exists():
            shutil.rmtree(repo_dir)

        try:
            # Clone the repository
            print(f"Cloning {clone_url}...")
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, str(repo_dir)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Git clone failed: {result.stderr}"
                }

            print(f"Successfully cloned to {repo_dir}")

            return {
                "success": True,
                "local_path": str(repo_dir),
                "owner": owner,
                "repo": repo,
                "github_url": github_url
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Clone timed out (max 5 minutes). Repository might be too large."
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Git is not installed. Please install git to clone repositories."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def cleanup_repository(self, local_path: str):
        """
        Remove cloned repository to free up space

        Args:
            local_path: Path to cloned repository
        """
        try:
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
                print(f"Cleaned up {local_path}")
        except Exception as e:
            print(f"Warning: Could not cleanup {local_path}: {e}")

    def get_workspace_size(self) -> int:
        """
        Get total size of workspace directory in bytes

        Returns:
            Size in bytes
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.workspace_dir):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size

    def cleanup_workspace(self):
        """
        Clean up entire workspace directory
        """
        try:
            if self.workspace_dir.exists():
                shutil.rmtree(self.workspace_dir)
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
                print(f"Cleaned up workspace: {self.workspace_dir}")
        except Exception as e:
            print(f"Warning: Could not cleanup workspace: {e}")


def test_github_cloner():
    """Test function"""
    cloner = GitHubCloner()

    # Test URL validation
    print("Testing URL validation...")
    test_urls = [
        "https://github.com/spring-projects/spring-petclinic",
        "https://github.com/invalid",
        "https://google.com/something",
        "not-a-url"
    ]

    for url in test_urls:
        result = cloner.validate_github_url(url)
        print(f"  {url}: {'Valid' if result['valid'] else 'Invalid - ' + result['error']}")

    # Test cloning (with a small repo)
    print("\nTesting clone...")
    test_repo = "https://github.com/spring-projects/spring-petclinic"
    clone_result = cloner.clone_repository(test_repo)

    if clone_result["success"]:
        print(f"  Clone successful: {clone_result['local_path']}")
        print(f"  Owner: {clone_result['owner']}, Repo: {clone_result['repo']}")
    else:
        print(f"  Clone failed: {clone_result['error']}")


if __name__ == "__main__":
    test_github_cloner()
