import os
import subprocess
import sys

def install_requirements():
    """Install required Python packages using pip."""
    print("Installing required Python packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        sys.exit(1)

def initialize_submodules():
    """Initialize and update the git submodules."""
    print("Initializing and updating Git submodules...")
    try:
        subprocess.check_call(["git", "submodule", "update", "--init", "--recursive", "src/submodules"])
        print("Git submodules initialized and updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize submodules: {e}")
        sys.exit(1)

def install_package():
    """Install the package in the current environment."""
    print("Installing the package...")
    try:
        subprocess.check_call([sys.executable, "setup.py", "install"])
        print("Package installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install the package: {e}")
        sys.exit(1)

def main():
    """Run the installation process."""
    if os.path.exists("requirements.txt"):
        install_requirements()
    else:
        print("No requirements.txt file found. Skipping Python package installation.")

    if os.path.isdir("src"):
        initialize_submodules()
    else:
        print("No src directory found. Skipping submodule initialization.")

    install_package()

if __name__ == "__main__":
    main()
