"""GitHub client for cloning and analyzing remote repositories."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import uuid
import stat
from pathlib import Path
from typing import Optional
from git import Repo
import requests
from github import Github, GithubException

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub repositories."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (optional but recommended)
        """
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.github = Github(self.token) if self.token else None
        # Utiliser un dossier temporaire unique avec UUID pour éviter les conflits
        self.session_id = uuid.uuid4().hex[:8]
        self.temp_dir = Path(tempfile.gettempdir()) / f"github_scans_{self.session_id}"
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"GitHub temp directory: {self.temp_dir}")
    
    def _force_remove(self, path: Path):
        """Force remove a file or directory (handles Windows permission issues)."""
        if not path.exists():
            return
        
        def on_rm_error(func, path, exc_info):
            """Handle permission errors by changing file attributes."""
            try:
                # Clear read-only flag and retry
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception as e:
                logger.warning(f"Could not remove {path}: {e}")
        
        try:
            if path.is_file():
                path.chmod(stat.S_IWRITE)
                path.unlink()
            else:
                shutil.rmtree(path, onerror=on_rm_error, ignore_errors=True)
        except Exception as e:
            logger.warning(f"Failed to force remove {path}: {e}")
    
    def clone_repository(self, repo_url: str, branch: str = "main") -> str:
        """
        Clone a GitHub repository locally.
        
        Args:
            repo_url: GitHub repository URL (https://github.com/user/repo.git)
            branch: Branch to clone (default: main)
        
        Returns:
            Local path to cloned repository
        """
        # Extraire le nom du repo pour le dossier
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        local_path = self.temp_dir / repo_name
        
        # Supprimer si existe déjà avec force
        if local_path.exists():
            logger.info(f"Removing existing directory: {local_path}")
            self._force_remove(local_path)
        
        # Si le chemin existe toujours, utiliser un nom alternatif
        if local_path.exists():
            local_path = self.temp_dir / f"{repo_name}_{uuid.uuid4().hex[:4]}"
        
        logger.info(f"Cloning {repo_url} (branch: {branch}) to {local_path}")
        
        try:
            # Cloner le dépôt
            if self.token:
                # Utiliser le token pour l'authentification
                authenticated_url = repo_url.replace(
                    "https://github.com",
                    f"https://{self.token}@github.com"
                )
                Repo.clone_from(authenticated_url, local_path, branch=branch, depth=1)
            else:
                # Clone public sans auth (depth=1 pour plus de vitesse)
                Repo.clone_from(repo_url, local_path, branch=branch, depth=1)
            
            logger.info(f"Successfully cloned {repo_name}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to clone {repo_url}: {e}")
            # Nettoyer en cas d'échec
            self._force_remove(local_path)
            raise
    
    def clone_repository_from_api(self, owner: str, repo_name: str, branch: str = "main") -> str:
        """
        Clone repository using owner and repo name.
        
        Args:
            owner: GitHub username or organization
            repo_name: Repository name
            branch: Branch to clone
        
        Returns:
            Local path to cloned repository
        """
        repo_url = f"https://github.com/{owner}/{repo_name}.git"
        return self.clone_repository(repo_url, branch)
    
    def get_repository_info(self, repo_url: str) -> dict:
        """
        Get information about a repository.
        
        Args:
            repo_url: GitHub repository URL
        
        Returns:
            Dictionary with repository information
        """
        if not self.github:
            return {"error": "GitHub token required for API access"}
        
        try:
            # Extraire owner/repo
            parts = repo_url.rstrip("/").split("/")
            if "github.com" in repo_url:
                idx = parts.index("github.com")
                owner = parts[idx + 1]
                repo_name = parts[idx + 2]
            else:
                owner, repo_name = parts[-2], parts[-1]
            
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "languages": {lang.name: lang.size for lang in repo.get_languages()},
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "open_issues": repo.open_issues_count,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "clone_url": repo.clone_url,
                "ssh_url": repo.ssh_url
            }
        except GithubException as e:
            logger.error(f"Failed to get repo info: {e}")
            return {"error": str(e)}
    
    def cleanup(self, local_path: str):
        """Remove cloned repository with force option."""
        try:
            path = Path(local_path)
            if path.exists():
                self._force_remove(path)
                logger.info(f"Cleaned up {local_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {local_path}: {e}")
    
    def cleanup_all(self):
        """Clean up the entire temporary directory for this session."""
        try:
            if self.temp_dir.exists():
                self._force_remove(self.temp_dir)
                logger.info(f"Cleaned up all temporary files: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp dir {self.temp_dir}: {e}")
    
    def list_available_branches(self, repo_url: str) -> list[str]:
        """List available branches in repository."""
        try:
            # Extraire owner/repo
            if "github.com" in repo_url:
                parts = repo_url.rstrip("/").split("/")
                idx = parts.index("github.com")
                owner = parts[idx + 1]
                repo_name = parts[idx + 2].replace(".git", "")
            else:
                owner, repo_name = repo_url.split("/")[-2], repo_url.split("/")[-1].replace(".git", "")
            
            if self.github:
                repo = self.github.get_repo(f"{owner}/{repo_name}")
                branches = [branch.name for branch in repo.get_branches()]
                return branches
            else:
                # Fallback: via API publique
                url = f"https://api.github.com/repos/{owner}/{repo_name}/branches"
                response = requests.get(url)
                if response.status_code == 200:
                    return [branch["name"] for branch in response.json()]
                return ["main", "master"]  # Default fallback
                
        except Exception as e:
            logger.error(f"Failed to list branches: {e}")
            return ["main", "master"]


# Singleton instance
_github_client = None

def get_github_client() -> GitHubClient:
    """Get or create GitHub client instance."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client