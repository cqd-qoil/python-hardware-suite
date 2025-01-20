from setuptools import setup, find_packages

# Read requirements from requirements.txt
def parse_requirements(filename="requirements.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]

# Set up the package
setup(
    name="hardware_suite",  # The name of your package
    version="0.1",  # Version of the package
    packages=find_packages(where="src"),  # Automatically find packages in the src directory
    package_dir={"": "src"},  # Tell setuptools that the package source code is under the src directory
    include_package_data=True,  # Include other data files if necessary (e.g., non-Python files)
    install_requires=find_packages(), #parse_requirements(),  # Install dependencies from requirements.txt
    zip_safe=False,  # Disable zip safe (may not be necessary, but often safe to set to False)
    entry_points={  # Optionally, define entry points for command line scripts if needed
        # Example entry point for a command line tool, if you have one
        # 'console_scripts': [
        #     'hardware_suite = hardware_suite.main_module:main_function',
        # ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",  # Specify minimum Python version
)
