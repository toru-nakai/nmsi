#!/usr/bin/env python3
"""nmsi - No More Search for Installation"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


# Constants
def get_nmsi_base_dir() -> Path:
    """Get NMSI_BASE_DIR. Use NMSI_PATH environment variable if set, otherwise use default"""
    nmsi_path = os.environ.get("NMSI_PATH")
    if nmsi_path:
        return Path(nmsi_path).expanduser()
    return Path.home() / ".local" / "share" / "nmsi"


NMSI_BASE_DIR = get_nmsi_base_dir()
INSTALL_DIR = NMSI_BASE_DIR / "install"
GITHUB_REPO = "https://github.com/toru-nakai/nmsi"

def get_os_type() -> str:
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


def get_arch() -> str:
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


def ensure_install_dir() -> Path:
    """Ensure installation directory exists"""
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    return INSTALL_DIR


def cmd_install(args: argparse.Namespace) -> int:
    """Implementation of install command"""
    tool_name = args.tool_name
    
    os_type = get_os_type()
    arch = get_arch()
    
    install_script_path = INSTALL_DIR / tool_name / os_type / arch / "install.sh"
    
    if not install_script_path.exists():
        print(f"Error: Installation script not found for {tool_name} on {os_type}/{arch}")
        print(f"Expected path: {install_script_path}")
        print(f"Run 'nmsi update' to download installation scripts.")
        return 1
    
    print(f"Installing {tool_name} for {os_type}/{arch}...")
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


def cmd_list(args: argparse.Namespace) -> int:
    """Implementation of list command"""
    ensure_install_dir()
    
    if not INSTALL_DIR.exists():
        print("No tools available. Run 'nmsi update' to download installation scripts.")
        return 0
    
    os_type = get_os_type()
    arch = get_arch()
    
    tools = []
    for tool_dir in INSTALL_DIR.iterdir():
        if tool_dir.is_dir():
            # Check if install script exists for current OS/architecture
            install_script_path = tool_dir / os_type / arch / "install.sh"
            if install_script_path.exists():
                tools.append(tool_dir.name)
    
    if not tools:
        print(f"No tools available for {os_type}/{arch}.")
        print("Run 'nmsi update' to download installation scripts.")
        return 0
    
    tools.sort()
    print(f"Available tools for {os_type}/{arch}:")
    for tool in tools:
        print(f"  - {tool}")
    
    return 0


def download_install_scripts(local_base: Path = INSTALL_DIR) -> int:
    """Download installation scripts from GitHub repository using git clone"""
    # Check if git command is available
    if not shutil.which("git"):
        raise RuntimeError("git command not found. Please install git.")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        repo_path = temp_path / "nmsi"
        
        print("Cloning repository...")
        try:
            # Clone only the latest commit with git clone --depth=1
            subprocess.run(
                ["git", "clone", "--depth=1", GITHUB_REPO, str(repo_path)],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")
        
        # Check if install directory exists
        install_dir = repo_path / "install"
        if not install_dir.exists():
            return 0
        
        # Copy all install.sh files in install directory
        downloaded_count = 0
        
        for install_script in install_dir.rglob("install.sh"):
            # Extract tool_name/os_type/arch from path
            # install/tool_name/os_type/arch/install.sh
            try:
                relative_path = install_script.relative_to(install_dir)
                parts = relative_path.parts
                
                if len(parts) >= 4:  # tool_name/os_type/arch/install.sh
                    tool_name = parts[0]
                    os_type = parts[1]
                    arch = parts[2]
                    
                    local_path = local_base / tool_name / os_type / arch / "install.sh"
                    
                    # Create directory and copy file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(install_script, local_path)
                    local_path.chmod(0o755)  # Make executable
                    
                    downloaded_count += 1
                    print(f"  ✓ {tool_name}/{os_type}/{arch}/install.sh")
            except Exception as e:
                print(f"  ✗ Failed to copy {install_script}: {e}")
        
        return downloaded_count


def cmd_update(args: argparse.Namespace) -> int:
    """Implementation of update command"""
    print("Updating installation scripts from GitHub...")
    print(f"Repository: {GITHUB_REPO}")
    print()
    
    ensure_install_dir()
    
    try:
        downloaded_count = download_install_scripts()
        
        if downloaded_count == 0:
            print("No installation scripts found in the repository.")
            print(f"Expected structure: install/<tool_name>/<os_type>/<arch>/install.sh")
            return 1
        
        print()
        print(f"Update completed. Downloaded {downloaded_count} script(s).")
        return 0
        
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_uninstall(args: argparse.Namespace) -> int:
    """Implementation of uninstall command"""
    print("Error: uninstall command is not yet implemented.")
    return 1


def cmd_add(args: argparse.Namespace) -> int:
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
    
    # Get OS/architecture (use provided values or auto-detect)
    os_type = args.os if args.os else get_os_type()
    arch = args.arch if args.arch else get_arch()
    
    # Determine destination path
    ensure_install_dir()
    dest_path = INSTALL_DIR / tool_name / os_type / arch / "install.sh"
    
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


def cmd_show(args: argparse.Namespace) -> int:
    """Implementation of show command"""
    tool_name = args.tool_name
    
    os_type = get_os_type()
    arch = get_arch()
    
    install_script_path = INSTALL_DIR / tool_name / os_type / arch / "install.sh"
    
    if not install_script_path.exists():
        print(f"Error: Installation script not found for {tool_name} on {os_type}/{arch}")
        print(f"Expected path: {install_script_path}")
        return 1
    
    try:
        script_content = install_script_path.read_text()
        print(f"# Installation script for {tool_name} ({os_type}/{arch})")
        print(f"# Path: {install_script_path}")
        print()
        print(script_content)
        return 0
    except Exception as e:
        print(f"Error: Failed to read script: {e}")
        return 1


def cmd_plugin(args: argparse.Namespace) -> int:
    """Implementation of plugin command"""
    print("Error: plugin command is not yet implemented.")
    return 1


def create_parser() -> argparse.ArgumentParser:
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
    install_parser.set_defaults(func=cmd_install)
    
    # list command
    list_parser = subparsers.add_parser(
        "list",
        help="List available tools"
    )
    list_parser.set_defaults(func=cmd_list)
    
    # update command
    update_parser = subparsers.add_parser(
        "update",
        help="Update installation scripts from GitHub"
    )
    update_parser.set_defaults(func=cmd_update)
    
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
    add_parser.set_defaults(func=cmd_add)
    
    # show command
    show_parser = subparsers.add_parser(
        "show",
        help="Show installation script content"
    )
    show_parser.add_argument(
        "tool_name",
        help="Name of the tool"
    )
    show_parser.set_defaults(func=cmd_show)
    
    # uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall a tool (not yet implemented)"
    )
    uninstall_parser.add_argument(
        "tool_name",
        help="Name of the tool to uninstall"
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
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
    plugin_parser.set_defaults(func=cmd_plugin)
    
    return parser


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
