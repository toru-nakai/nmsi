"""Downloader classes for various URL schemes"""

import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlretrieve


class Downloader(ABC):
    """Base class for downloaders"""
    
    def __init__(self, url: str, destination: Path):
        """
        Initialize downloader
        
        Args:
            url: URL to download from
            destination: Destination directory
        """
        self.url = url
        self.destination = destination
    
    @abstractmethod
    def download(self) -> int:
        """
        Download installation scripts from the URL
        
        Returns:
            0 on success, 1 on failure
        """
        pass
    
    def _copy_scripts(self, source_dir: Path, success_message: str = None) -> int:
        """
        Copy installation scripts from source to destination
        
        Args:
            source_dir: Source directory containing installation scripts
            success_message: Optional success message to print
            
        Returns:
            0 on success
            
        Raises:
            RuntimeError: If copying fails
        """
        try:
            # Ensure destination directory exists
            self.destination.mkdir(parents=True, exist_ok=True)
            
            # Copy all files from source install directory to destination
            for src_file in source_dir.rglob("*"):
                if src_file.is_file():
                    # Calculate relative path from install directory
                    rel_path = src_file.relative_to(source_dir)
                    dest_file = self.destination / rel_path
                    
                    # Create parent directory
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file (overwrite if exists, but don't delete existing files)
                    shutil.copy2(src_file, dest_file)
                    
                    # Make executable if it's a script
                    if dest_file.suffix == ".sh":
                        dest_file.chmod(0o755)
            
            if success_message:
                print(success_message)
            return 0
            
        except Exception as e:
            raise RuntimeError(f"Failed to copy scripts: {e}")
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL for git repositories
        
        - git:// URLs are converted to https://
        - git@ URLs (SSH) are kept as-is
        
        Args:
            url: Original URL
            
        Returns:
            Normalized URL
        """
        if url.startswith("git://"):
            # Convert git:// to https://
            return url.replace("git://", "https://", 1)
        # git@ URLs are kept as-is
        return url
    
    @staticmethod
    def create_downloader(url: str, destination: Path) -> "Downloader":
        """
        Create appropriate downloader instance based on URL scheme
        
        Args:
            url: URL to download from
            destination: Destination directory
            
        Returns:
            Downloader instance
            
        Raises:
            ValueError: If URL scheme is not supported
        """
        # Handle git@ SSH URLs first (before urlparse, as they don't have a scheme)
        if url.startswith("git@"):
            # git@ URLs are kept as-is (no normalization)
            return GitDownloader(url, destination)
        
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        
        # Handle git:// URLs (will be normalized to https://)
        if url.startswith("git://") or scheme == "git":
            normalized_url = Downloader.normalize_url(url)
            return GitDownloader(normalized_url, destination)
        
        if scheme in ("http", "https"):
            return HttpDownloader(url, destination)
        elif scheme == "file":
            return FileDownloader(url, destination)
        else:
            raise ValueError(f"Unsupported URL scheme: {scheme}")


class HttpDownloader(Downloader):
    """Downloader for HTTP/HTTPS URLs"""
    
    def download(self) -> int:
        """Download from HTTP/HTTPS URL"""
        try:
            print(f"Downloading from {self.url}...")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                
                # Download the file
                # For now, assume it's a zip or tar archive
                # We'll need to handle different formats
                archive_path = tmp_path / "archive"
                
                try:
                    urlretrieve(self.url, archive_path)
                except Exception as e:
                    raise RuntimeError(f"Failed to download from {self.url}: {e}")
                
                # Extract and copy installation scripts
                # This is a simplified version - you may need to handle different archive formats
                return self._extract_and_copy(archive_path)
                
        except Exception as e:
            print(f"Error: {e}")
            return 1
    
    def _extract_and_copy(self, archive_path: Path) -> int:
        """Extract archive and copy installation scripts"""
        # This is a placeholder - actual implementation depends on archive format
        # For now, we'll assume it's a directory structure similar to the git repo
        try:
            # Try to extract as zip
            if shutil.which("unzip"):
                subprocess.run(
                    ["unzip", "-q", str(archive_path), "-d", str(archive_path.parent)],
                    check=True,
                    capture_output=True
                )
            # Try to extract as tar
            elif shutil.which("tar"):
                subprocess.run(
                    ["tar", "xf", str(archive_path), "-C", str(archive_path.parent)],
                    check=True,
                    capture_output=True
                )
            else:
                raise RuntimeError("No extraction tool available (unzip or tar)")
            
            # Find install directory in extracted files
            extracted_dir = archive_path.parent
            install_dir = None
            
            for path in extracted_dir.rglob("install"):
                if path.is_dir():
                    install_dir = path
                    break
            
            if not install_dir:
                raise RuntimeError("install directory not found in archive")
            
            # Copy installation scripts
            return self._copy_scripts(install_dir, "Installation scripts downloaded successfully.")
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract archive: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Failed to process archive: {e}")


class FileDownloader(Downloader):
    """Downloader for file:// URLs"""
    
    def download(self) -> int:
        """Download from file:// URL"""
        try:
            parsed = urlparse(self.url)
            source_path = Path(parsed.path)
            
            if not source_path.exists():
                raise RuntimeError(f"File not found: {source_path}")
            
            print(f"Copying from {source_path}...")
            
            # Ensure destination directory exists
            self.destination.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                # Single file - copy to destination
                dest_file = self.destination / source_path.name
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_file)
                dest_file.chmod(0o755)
            elif source_path.is_dir():
                # Directory - copy install subdirectory if exists
                install_dir = source_path / "install"
                if install_dir.exists() and install_dir.is_dir():
                    self._copy_scripts(install_dir)
                else:
                    # Copy entire directory structure
                    self._copy_scripts(source_path)
            else:
                raise RuntimeError(f"Invalid source path: {source_path}")
            
            print("Installation scripts copied successfully.")
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1


class GitDownloader(Downloader):
    """Downloader for Git repositories"""
    
    def download(self) -> int:
        """Download from Git repository"""
        # Check if git command is available
        if not shutil.which("git"):
            raise RuntimeError("git command not found. Please install git.")
        
        try:
            print(f"Cloning repository from {self.url}...")
            
            # Create temporary directory for cloning
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                repo_path = tmp_path / "repo"
                
                # Clone repository
                try:
                    subprocess.run(
                        ["git", "clone", "--depth=1", self.url, str(repo_path)],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                except subprocess.CalledProcessError as e:
                    raise RuntimeError(f"Failed to clone repository: {e.stderr}")
                
                # Find install directory
                install_dir = repo_path / "install"
                
                if not install_dir.exists():
                    raise RuntimeError("install directory not found in repository")
                
                # Copy installation scripts
                return self._copy_scripts(install_dir, "Installation scripts downloaded successfully.")
                
        except Exception as e:
            print(f"Error: {e}")
            return 1
