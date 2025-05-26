#!/usr/bin/env python3
"""
Setup script for Blender MCP server.

This script helps users install and configure the Blender MCP server.
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_uv_installed():
    """Check if UV package manager is installed."""
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ UV installed: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ UV package manager not found")
    print("Install UV with:")
    if sys.platform == "darwin":  # macOS
        print("  brew install uv")
    elif sys.platform == "win32":  # Windows
        print('  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"')
    else:  # Linux
        print("  curl -LsSf https://astral.sh/uv/install.sh | sh")
    return False


def install_dependencies():
    """Install project dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run(['uv', 'sync'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def create_claude_config():
    """Create Claude Desktop configuration."""
    print("\n🤖 Setting up Claude Desktop configuration...")
    
    # Find Claude config directory
    if sys.platform == "darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "Claude"
    elif sys.platform == "win32":  # Windows
        config_dir = Path.home() / "AppData" / "Roaming" / "Claude"
    else:  # Linux
        config_dir = Path.home() / ".config" / "claude"
    
    config_file = config_dir / "claude_desktop_config.json"
    
    # Create config if it doesn't exist
    if not config_file.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        config = {"mcpServers": {}}
    else:
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {"mcpServers": {}}
    
    # Add Blender MCP server
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    config["mcpServers"]["blender"] = {
        "command": "uvx",
        "args": ["blender-mcp"]
    }
    
    # Write config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Claude config updated: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to update Claude config: {e}")
        return False


def create_cursor_config():
    """Create Cursor configuration."""
    print("\n🖱️ Setting up Cursor configuration...")
    
    cursor_dir = Path(".cursor")
    cursor_dir.mkdir(exist_ok=True)
    
    config_file = cursor_dir / "mcp.json"
    
    if sys.platform == "win32":  # Windows
        config = {
            "mcpServers": {
                "blender": {
                    "command": "cmd",
                    "args": ["/c", "uvx", "blender-mcp"]
                }
            }
        }
    else:  # macOS/Linux
        config = {
            "mcpServers": {
                "blender": {
                    "command": "uvx",
                    "args": ["blender-mcp"]
                }
            }
        }
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Cursor config created: {config_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create Cursor config: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Install the Blender addon:")
    print("   - Open Blender")
    print("   - Go to Edit > Preferences > Add-ons")
    print("   - Click 'Install...' and select 'blender_addon.py'")
    print("   - Enable the 'Blender MCP' addon")
    print("")
    print("2. Start the MCP server in Blender:")
    print("   - In Blender's 3D View, press 'N' to open the sidebar")
    print("   - Find the 'BlenderMCP' tab")
    print("   - Click 'Start MCP Server'")
    print("")
    print("3. Test the connection:")
    print("   - Run: python test_server.py")
    print("")
    print("4. Use with your AI assistant:")
    print("   - Claude Desktop: Restart Claude to load the new config")
    print("   - Cursor: The MCP server should be available in settings")
    print("")
    print("5. Try some commands:")
    print("   - 'Create a red cube in Blender'")
    print("   - 'Set up studio lighting'")
    print("   - 'Position the camera for an isometric view'")


def main():
    """Main setup function."""
    print("🚀 Blender MCP Server Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_python_version():
        return 1
    
    if not check_uv_installed():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create configurations
    claude_success = create_claude_config()
    cursor_success = create_cursor_config()
    
    if not (claude_success or cursor_success):
        print("⚠️  Could not create AI assistant configurations")
        print("You may need to configure them manually")
    
    print_next_steps()
    return 0


if __name__ == "__main__":
    sys.exit(main()) 