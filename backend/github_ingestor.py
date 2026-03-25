import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class GitHubIngestor:
    def __init__(self, github_url: str):
        self.github_url = github_url
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

    def clone(self) -> str:
        """Clones the repository and returns the path to the cloned directory."""
        try:
            subprocess.check_call(["git", "clone", "--depth", "1", self.github_url, self.repo_path])
            return self.repo_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise RuntimeError(f"Failed to clone repository {self.github_url}") from e

    def cleanup(self):
        """Cleans up the temporary directory."""
        self.temp_dir.cleanup()

    def __enter__(self):
        self.clone()
        return self.repo_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
