#!/usr/bin/env python3
"""
Setup script for NL to SQL Converter
Run this script to set up the development environment
"""

import os
import sys
import subprocess
import platform

def run_command(command, check=True):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        print(f"✅ {command}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running: {command}")
        print(f"Error: {e.stderr}")
        return None

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("Please install Python 3.8 or higher")
        return False

def create_virtual_environment():
    """Create a virtual environment"""
    print("\n🔧 Creating virtual environment...")
    
    # Check if venv already exists
    if os.path.exists("venv"):
        print("⚠️  Virtual environment already exists")
        return True
    
    # Create venv
    result = run_command("python -m venv venv")
    if result:
        print("✅ Virtual environment created successfully")
        return True
    return False

def activate_and_install():
    """Activate virtual environment and install dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Determine activation command based on OS
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install requirements
    result = run_command(f"{pip_cmd} install -r requirements.txt")
    if result:
        print("✅ Dependencies installed successfully")
        return True
    return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        ".streamlit"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def create_secrets_file():
    """Create secrets template if it doesn't exist"""
    secrets_path = ".streamlit/secrets.toml"
    
    if not os.path.exists(secrets_path):
        with open(secrets_path, 'w') as f:
            f.write("""# Hugging Face Token (Optional - for better API rate limits)
# Get your free token from https://huggingface.co/settings/tokens
HUGGINGFACE_TOKEN = "your_huggingface_token_here"

# Note: This file should be kept private and not committed to version control
# Add .streamlit/secrets.toml to your .gitignore file
""")
        print(f"✅ Created secrets template: {secrets_path}")
        print("🔑 Remember to add your Hugging Face token for better performance!")
    else:
        print(f"📄 Secrets file already exists: {secrets_path}")

def print_usage_instructions():
    """Print instructions for running the app"""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
    else:
        activate_cmd = "source venv/bin/activate"
    
    print(f"""
🚀 To run the application:

1. Activate the virtual environment:
   {activate_cmd}

2. Run the Streamlit app:
   streamlit run app.py

3. Open your browser to:
   http://localhost:8501

📋 Optional Configuration:
- Edit .streamlit/secrets.toml to add your Hugging Face token
- Modify .streamlit/config.toml for custom themes

🌐 For deployment:
- Streamlit Cloud: Push to GitHub and deploy at share.streamlit.io
- Vercel: Run 'vercel --prod' after installing Vercel CLI
- Hugging Face Spaces: Upload files to a new Streamlit Space

💡 Need help? Check README.md for detailed instructions!
""")

def main():
    """Main setup function"""
    print("🔍 NL to SQL Converter - Setup Script")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create virtual environment
    if not create_virtual_environment():
        print("❌ Failed to create virtual environment")
        sys.exit(1)
    
    # Install dependencies
    if not activate_and_install():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create secrets file
    create_secrets_file()
    
    # Print usage instructions
    print_usage_instructions()

if __name__ == "__main__":
    main()