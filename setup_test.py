#!/usr/bin/env python3
"""Setup and test script for Prombank MCP."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print('='*50)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout:
                print("Output:", result.stdout[:500])
        else:
            print(f"❌ Failed: {description}")
            print("Error:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


def main():
    """Main setup and test function."""
    print("🚀 Setting up Prombank MCP...")
    
    # Install in development mode
    if not run_command("pip install -e .", "Installing package in development mode"):
        print("❌ Failed to install package. Please install manually with: pip install -e .")
        return
    
    # Initialize database
    if not run_command("python -m prombank.cli init", "Initializing database"):
        print("❌ Failed to initialize database.")
        return
    
    # Create test prompt
    test_prompt_content = '''
    You are a helpful AI assistant. Please help the user with their request.
    Be concise, accurate, and provide practical solutions.
    '''
    
    create_cmd = f'python -m prombank.cli prompt create --title "Test Assistant Prompt" --content "{test_prompt_content.strip()}" --category "General" --tags "assistant,helper"'
    
    if run_command(create_cmd, "Creating test prompt"):
        print("✅ Test prompt created successfully!")
    
    # List prompts to verify
    run_command("python -m prombank.cli prompt list", "Listing all prompts")
    
    # Test search
    run_command('python -m prombank.cli prompt list --search "assistant"', "Searching prompts")
    
    print("\n" + "="*60)
    print("🎉 Setup completed!")
    print("\nNext steps:")
    print("1. Start the MCP server: prombank mcp-server")
    print("2. Start the API server: prombank server")
    print("3. View API docs: http://localhost:8000/docs")
    print("4. Use CLI: prombank --help")
    print("\nFor Cursor integration, add this to your MCP config:")
    print("""
{
  "prombank-mcp": {
    "command": "prombank",
    "args": ["mcp-server"]
  }
}
    """)


if __name__ == "__main__":
    main()