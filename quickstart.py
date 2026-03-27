#!/usr/bin/env python
"""
Quick start guide for testing the Salla API MCP Server.
Run this script to verify your setup is working.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and report results."""
    print(f"\n📋 {description}")
    print(f"   Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"      {line}")
            return True
        else:
            print(f"   ❌ Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_setup():
    """Check setup requirements."""
    print("\n" + "=" * 70)
    print("  Salla API MCP Server - Quick Start Verification")
    print("=" * 70)
    
    checks = {
        "Python 3.8+": "python --version",
        "Required files": "test -f server.py && test -f openapi.json && test -f requirements.txt",
    }
    
    passed = 0
    for check_name, cmd in checks.items():
        if run_command(cmd, f"Checking: {check_name}"):
            passed += 1
        else:
            print(f"   ⚠️  {check_name} check failed")
    
    print(f"\n✓ Passed {passed}/{len(checks)} checks")
    
    return passed == len(checks)


def install_dependencies():
    """Install Python dependencies."""
    print("\n" + "=" * 70)
    print("  Installing Dependencies")
    print("=" * 70)
    
    if sys.platform == "win32":
        venv_activate = "venv\\Scripts\\activate"
    else:
        venv_activate = "source venv/bin/activate"
    
    steps = [
        ("Creating virtual environment", f"python -m venv venv"),
        ("Installing dependencies", f"{venv_activate} && pip install -r requirements.txt"),
    ]
    
    for step_name, cmd in steps:
        if not run_command(cmd, step_name):
            print(f"❌ Failed at: {step_name}")
            return False
    
    return True


def setup_env():
    """Setup environment file."""
    print("\n" + "=" * 70)
    print("  Setting Up Environment")
    print("=" * 70)
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("\n📋 Copying .env.example to .env")
            with open(env_example) as src:
                content = src.read()
            with open(env_file, 'w') as dst:
                dst.write(content)
            print("✅ .env file created")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file already exists")
    
    print(f"\n⚠️  IMPORTANT: Edit .env and set your SALLA_API_TOKEN")
    print(f"   File location: {env_file.absolute()}")
    
    return True


def run_test():
    """Run the test suite."""
    print("\n" + "=" * 70)
    print("  Running Tests")
    print("=" * 70)
    
    print("\n🧪 Testing search functionality...")
    return run_command("python test_server.py", "Running test suite")


def show_next_steps():
    """Show next steps."""
    print("\n" + "=" * 70)
    print("  Next Steps")
    print("=" * 70)
    
    print("""
✅ Setup complete! Here's what to do next:

1. Configure Your API Token
   - Edit .env file with your SALLA_API_TOKEN
   - Get token from: https://developer.salla.dev/

2. Start the MCP Server
   - Activate venv: source venv/bin/activate (or venv\\Scripts\\activate on Windows)
   - Run: python server.py
   - You should see "Loaded OpenAPI spec from ./openapi.json"

3. Connect with an MCP Client
   - Option A: VS Code Copilot Agent Mode
     → See VSCODE_SETUP.md for instructions
   
   - Option B: Command line testing
     → Place your MCP client commands here
     → Example: mcp-cli call-tool salla-api search --query "products"

4. Example Usage with Agent
   - Start the server in one terminal: python server.py
   - In VS Code with Copilot, ask:
     "Search for products and show me the first 5"

📚 Documentation:
   - README.md - Full documentation and architecture
   - VSCODE_SETUP.md - VS Code integration guide
   - test_server.py - Testing examples

🆘 Troubleshooting:
   - Check README.md Troubleshooting section
   - Verify .env has correct SALLA_API_TOKEN
   - Ensure openapi.json exists in project root
    """)


def main():
    """Main setup flow."""
    try:
        # Check prerequisites
        if not check_setup():
            print("\n❌ Setup check failed. Please fix the issues above.")
            sys.exit(1)
        
        # Install dependencies
        print("\n" + "=" * 70)
        response = input("Install dependencies? (y/n): ")
        if response.lower() == 'y':
            if not install_dependencies():
                print("\n❌ Installation failed.")
                sys.exit(1)
        
        # Setup environment
        if not setup_env():
            print("\n❌ Environment setup failed.")
            sys.exit(1)
        
        # Run tests
        print("\n" + "=" * 70)
        response = input("Run tests? (y/n): ")
        if response.lower() == 'y':
            run_test()
        
        # Show next steps
        show_next_steps()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
