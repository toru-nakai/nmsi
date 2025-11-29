#!/usr/bin/env python3
"""nmsi - No More Search for Installation"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
        detected_os_type, detected_flavors = self._detect_os_and_flavors()
        if os_type:
            normalized_os = os_type.lower()
            self.os_type = normalized_os
            self.os_flavors = [normalized_os]
            if normalized_os != "linux":
                self.os_flavors.append("linux")
        else:
            self.os_type = detected_os_type
            self.os_flavors = detected_flavors
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
    
    def _detect_os_and_flavors(self) -> Tuple[str, List[str]]:
        """Get OS type and ordered list of flavor fallbacks"""
        system = platform.system().lower()
        if system == "darwin":
            return "macos", ["macos"]
        elif system == "linux":
            flavors = self._detect_linux_flavors()
            primary = flavors[0] if flavors else "linux"
            return primary, flavors or ["linux"]
        elif system == "windows":
            return "windows", ["windows"]
        else:
            return system, [system]

    @staticmethod
    def _detect_linux_flavors() -> List[str]:
        """Detect Linux distribution flavors ordered by specificity"""
        info = {}
        try:
            info = platform.freedesktop_os_release()
        except (AttributeError, FileNotFoundError):
            info = NMSI._read_os_release_file()

        flavors: List[str] = []
        base_id = info.get("ID", "linux").lower()
        version_id = info.get("VERSION_ID", "").strip().strip('"')
        version_major = version_id.split(".")[0] if version_id else ""

        def add_flavor(name: str):
            if name and name not in flavors:
                flavors.append(name)

        if base_id:
            if version_major:
                add_flavor(f"{base_id}{version_major}")
            add_flavor(base_id)

        id_like = info.get("ID_LIKE", "")
        if id_like:
            for like in id_like.split():
                like = like.lower()
                if version_major:
                    add_flavor(f"{like}{version_major}")
                add_flavor(like)

        add_flavor("linux")
        return flavors

    @staticmethod
    def _read_os_release_file() -> Dict[str, str]:
        """Read /etc/os-release style file into dict"""
        paths = [Path("/etc/os-release"), Path("/usr/lib/os-release")]
        for path in paths:
            if not path.exists():
                continue
            data: Dict[str, str] = {}
            try:
                for line in path.read_text().splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, value = line.split("=", 1)
                    value = value.strip().strip('"')
                    data[key] = value
                if data:
                    return data
            except OSError:
                continue
        return {}
    
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

    def _find_install_script(self, tool_name: str) -> Tuple[Optional[Path], Optional[str], Optional[str]]:
        """
        Find install script path considering OS flavor and architecture fallbacks.
        
        Search priority:
        1. {tool_name}/{os}/{arch}/install.sh (OS/architecture specific)
        2. {tool_name}/{os}/general/install.sh (OS specific, architecture independent)
        3. {tool_name}/universal/{arch}/install.sh (OS independent, architecture specific)
        4. {tool_name}/universal/general/install.sh (OS/architecture independent)
        """
        for os_name in self.os_flavors:
            install_script_path = self.install_dir / tool_name / os_name / self.arch / "install.sh"
            if install_script_path.exists():
                return install_script_path, os_name, self.arch
            general_script_path = self.install_dir / tool_name / os_name / "general" / "install.sh"
            if general_script_path.exists():
                return general_script_path, os_name, "general"
        
        universal_arch_path = self.install_dir / tool_name / "universal" / self.arch / "install.sh"
        if universal_arch_path.exists():
            return universal_arch_path, "universal", self.arch
        universal_general_path = self.install_dir / tool_name / "universal" / "general" / "install.sh"
        if universal_general_path.exists():
            return universal_general_path, "universal", "general"
        
        return None, None, None
    
    def cmd_install(self, args: argparse.Namespace) -> int:
        """Implementation of install command"""
        tool_name = args.tool_name

        install_script_path, resolved_os, resolved_arch = self._find_install_script(tool_name)

        if not install_script_path:
            expected_path = self.install_dir / tool_name / self.os_type / self.arch / "install.sh"
            print(f"Error: Installation script not found for {tool_name} on {self.os_type}/{self.arch}")
            print(f"Expected primary path: {expected_path}")
            print(f"Tried OS flavors: {', '.join(self.os_flavors)}")
            print(f"Run 'nmsi update' to download installation scripts.")
            return 1

        print(f"Installing {tool_name} for {resolved_os}/{resolved_arch}...")
        if resolved_os != self.os_type:
            print(f"Note: Falling back from {self.os_type} to {resolved_os}.")
        if resolved_arch != self.arch:
            print(f"Note: Falling back from {self.arch} to {resolved_arch}.")
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
        
        if args.all:
            # List all tools regardless of OS/architecture
            tools = []
            for tool_dir in self.install_dir.iterdir():
                if tool_dir.is_dir():
                    # Check if any install script exists
                    has_script = False
                    for os_dir in tool_dir.iterdir():
                        if os_dir.is_dir():
                            for arch_dir in os_dir.iterdir():
                                if arch_dir.is_dir():
                                    script_path = arch_dir / "install.sh"
                                    if script_path.exists():
                                        has_script = True
                                        break
                            if has_script:
                                break
                    if has_script:
                        tools.append(tool_dir.name)
            
            if not tools:
                print("No tools available. Run 'nmsi update' to download installation scripts.")
                return 0
            
            tools.sort()
            print("All available tools:")
            for tool in tools:
                print(f"  - {tool}")
        else:
            # List tools for current OS/architecture
            tools = []
            for tool_dir in self.install_dir.iterdir():
                if tool_dir.is_dir():
                    # Check if install script exists for current OS/architecture
                    install_script_path, _, _ = self._find_install_script(tool_dir.name)
                    if install_script_path:
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
        
        install_script_path, resolved_os, resolved_arch = self._find_install_script(tool_name)
        
        if not install_script_path:
            expected_path = self.install_dir / tool_name / self.os_type / self.arch / "install.sh"
            print(f"Error: Installation script not found for {tool_name} on {self.os_type}/{self.arch}")
            print(f"Expected primary path: {expected_path}")
            print(f"Tried OS flavors: {', '.join(self.os_flavors)}")
            return 1
        
        try:
            script_content = install_script_path.read_text()
            print(f"# Installation script for {tool_name} ({resolved_os}/{resolved_arch})")
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
        list_parser.add_argument(
            "-a", "--all",
            action="store_true",
            help="List all tools regardless of OS/architecture"
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
