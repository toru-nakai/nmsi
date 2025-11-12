#!/usr/bin/env python3
"""nmsi - No More Search for Installation"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from downloader import Downloader


class NMSI:
    """No More Search for Installation - Main class"""
    
    def __init__(self, os_type: Optional[str] = None, arch: Optional[str] = None):
        """
        Initialize NMSI instance
        
        Args:
            os_type: OS type (default: auto-detect)
            arch: Architecture (default: auto-detect)
        """
        self.os_type = os_type if os_type else self._get_os_type()
        self.arch = arch if arch else self._get_arch()
        self.base_dir = self._get_nmsi_base_dir()
        self.install_dir = self.base_dir / "install"
        self.github_repo = "git://github.com/toru-nakai/nmsi"
    
    @staticmethod
    def _get_nmsi_base_dir() -> Path:
        """Get NMSI_BASE_DIR. Use NMSI_PATH environment variable if set, otherwise use default"""
        nmsi_path = os.environ.get("NMSI_PATH")
        if nmsi_path:
            return Path(nmsi_path).expanduser()
        return Path.home() / ".local" / "share" / "nmsi"
    
    @staticmethod
    def _get_os_type() -> str:
        """Get OS type"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        elif system == "windows":
            return "windows"
        else:
            return system
    
    @staticmethod
    def _get_arch() -> str:
        """Get architecture"""
        machine = platform.machine().lower()
        # Normalize common architecture names
        if machine in ["x86_64", "amd64"]:
            return "amd64"
        elif machine in ["aarch64", "arm64"]:
            return "arm64"
        elif machine.startswith("arm"):
            return "arm"
        elif machine == "i386" or machine == "i686":
            return "i386"
        else:
            return machine
    
    def _ensure_install_dir(self) -> Path:
        """Ensure installation directory exists"""
        self.install_dir.mkdir(parents=True, exist_ok=True)
        return self.install_dir
    
    def cmd_install(self, args: argparse.Namespace) -> int:
        """Implementation of install command"""
        tool_name = args.tool_name
        
        install_script_path = self.install_dir / tool_name / self.os_type / self.arch / "install.sh"
        
        if not install_script_path.exists():
            print(f"Error: Installation script not found for {tool_name} on {self.os_type}/{self.arch}")
            print(f"Expected path: {install_script_path}")
            print(f"Run 'nmsi update' to download installation scripts.")
            return 1
        
        print(f"Installing {tool_name} for {self.os_type}/{self.arch}...")
        print(f"Running: {install_script_path}")
        
        # Execute the script
        try:
            result = subprocess.run(
                ["bash", str(install_script_path)],
                check=True,
                cwd=install_script_path.parent
            )
            print(f"Successfully installed {tool_name}")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"Error: Installation failed with exit code {e.returncode}")
            return 1
        except FileNotFoundError:
            print("Error: bash not found. Please install bash.")
            return 1
    
    def cmd_list(self, args: argparse.Namespace) -> int:
        """Implementation of list command"""
        self._ensure_install_dir()
        
        if not self.install_dir.exists():
            print("No tools available. Run 'nmsi update' to download installation scripts.")
            return 0
        
        tools = []
        for tool_dir in self.install_dir.iterdir():
            if tool_dir.is_dir():
                # Check if install script exists for current OS/architecture
                install_script_path = tool_dir / self.os_type / self.arch / "install.sh"
                if install_script_path.exists():
                    tools.append(tool_dir.name)
        
        if not tools:
            print(f"No tools available for {self.os_type}/{self.arch}.")
            print("Run 'nmsi update' to download installation scripts.")
            return 0
        
        tools.sort()
        print(f"Available tools for {self.os_type}/{self.arch}:")
        for tool in tools:
            print(f"  - {tool}")
        
        return 0
    
    def cmd_update(self, args: argparse.Namespace) -> int:
        """Implementation of update command"""
        if args.from_url:
            # Download from specified URL
            print(f"Downloading installation scripts from {args.from_url}...")
            print(f"Destination: {self.install_dir}")
            print()
            
            try:
                downloader = Downloader.create_downloader(args.from_url, self.install_dir)
                result = downloader.download()
                
                if result == 0:
                    print()
                    print("Update completed.")
                return result
                
            except ValueError as e:
                print(f"Error: {e}")
                return 1
            except RuntimeError as e:
                print(f"Error: {e}")
                return 1
            except Exception as e:
                print(f"Error: {e}")
                return 1
        else:
            # Default: download from GitHub
            print("Updating installation scripts from GitHub...")
            print(f"Repository: {self.github_repo}")
            print(f"Destination: {self.install_dir}")
            print()
            
            try:
                downloader = Downloader.create_downloader(self.github_repo, self.install_dir)
                result = downloader.download()
                
                if result == 0:
                    print()
                    print("Update completed.")
                return result
                
            except ValueError as e:
                print(f"Error: {e}")
                return 1
            except RuntimeError as e:
                print(f"Error: {e}")
                return 1
            except Exception as e:
                print(f"Error: {e}")
                return 1
    
    def cmd_uninstall(self, args: argparse.Namespace) -> int:
        """Implementation of uninstall command"""
        print("Error: uninstall command is not yet implemented.")
        return 1
    
    def cmd_add(self, args: argparse.Namespace) -> int:
        """Implementation of add command"""
        tool_name = args.name
        script_path = Path(args.script)
        
        # Check if script file exists
        if not script_path.exists():
            print(f"Error: Script file not found: {script_path}")
            return 1
        
        if not script_path.is_file():
            print(f"Error: Not a file: {script_path}")
            return 1
        
        # Get OS/architecture (use provided values or instance values)
        os_type = args.os if args.os else self.os_type
        arch = args.arch if args.arch else self.arch
        
        # Determine destination path
        self._ensure_install_dir()
        dest_path = self.install_dir / tool_name / os_type / arch / "install.sh"
        
        # Create directory
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        try:
            shutil.copy2(script_path, dest_path)
            dest_path.chmod(0o755)  # Make executable
            
            print(f"Added script for {tool_name} ({os_type}/{arch})")
            print(f"  Source: {script_path}")
            print(f"  Destination: {dest_path}")
            return 0
        except Exception as e:
            print(f"Error: Failed to copy script: {e}")
            return 1
    
    def cmd_show(self, args: argparse.Namespace) -> int:
        """Implementation of show command"""
        tool_name = args.tool_name
        
        install_script_path = self.install_dir / tool_name / self.os_type / self.arch / "install.sh"
        
        if not install_script_path.exists():
            print(f"Error: Installation script not found for {tool_name} on {self.os_type}/{self.arch}")
            print(f"Expected path: {install_script_path}")
            return 1
        
        try:
            script_content = install_script_path.read_text()
            print(f"# Installation script for {tool_name} ({self.os_type}/{self.arch})")
            print(f"# Path: {install_script_path}")
            print()
            print(script_content)
            return 0
        except Exception as e:
            print(f"Error: Failed to read script: {e}")
            return 1
    
    def cmd_plugin(self, args: argparse.Namespace) -> int:
        """Implementation of plugin command"""
        print("Error: plugin command is not yet implemented.")
        return 1
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create CLI parser"""
        parser = argparse.ArgumentParser(
            prog="nmsi",
            description="No More Search for Installation - Easy installation tool for open source software"
        )
        
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # install command
        install_parser = subparsers.add_parser(
            "install",
            help="Install a tool"
        )
        install_parser.add_argument(
            "tool_name",
            help="Name of the tool to install"
        )
        install_parser.set_defaults(func=self.cmd_install)
        
        # list command
        list_parser = subparsers.add_parser(
            "list",
            help="List available tools"
        )
        list_parser.set_defaults(func=self.cmd_list)
        
        # update command
        update_parser = subparsers.add_parser(
            "update",
            help="Update installation scripts from GitHub or specified URL"
        )
        update_parser.add_argument(
            "--from",
            dest="from_url",
            metavar="URL",
            help="Download installation scripts from specified URL (supports http, https, file, git)"
        )
        update_parser.set_defaults(func=self.cmd_update)
        
        # add command
        add_parser = subparsers.add_parser(
            "add",
            help="Add an installation script for a tool"
        )
        add_parser.add_argument(
            "--name",
            required=True,
            help="Name of the tool"
        )
        add_parser.add_argument(
            "--os",
            help="OS type (default: auto-detect)"
        )
        add_parser.add_argument(
            "--arch",
            help="Architecture (default: auto-detect)"
        )
        add_parser.add_argument(
            "script",
            help="Path to the installation script file"
        )
        add_parser.set_defaults(func=self.cmd_add)
        
        # show command
        show_parser = subparsers.add_parser(
            "show",
            help="Show installation script content"
        )
        show_parser.add_argument(
            "tool_name",
            help="Name of the tool"
        )
        show_parser.set_defaults(func=self.cmd_show)
        
        # uninstall command
        uninstall_parser = subparsers.add_parser(
            "uninstall",
            help="Uninstall a tool (not yet implemented)"
        )
        uninstall_parser.add_argument(
            "tool_name",
            help="Name of the tool to uninstall"
        )
        uninstall_parser.set_defaults(func=self.cmd_uninstall)
        
        # plugin command
        plugin_parser = subparsers.add_parser(
            "plugin",
            help="Manage plugins (not yet implemented)"
        )
        plugin_parser.add_argument(
            "plugin_name",
            nargs="?",
            help="Plugin name"
        )
        plugin_parser.set_defaults(func=self.cmd_plugin)
        
        return parser
    
    def run(self, args: Optional[argparse.Namespace] = None) -> int:
        """
        Run NMSI with parsed arguments
        
        Args:
            args: Parsed arguments (if None, will parse from sys.argv)
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        parser = self.create_parser()
        if args is None:
            args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 1
        
        return args.func(args)


def main() -> int:
    """Main entry point"""
    nmsi = NMSI()
    return nmsi.run()


if __name__ == "__main__":
    sys.exit(main())
