"""
Book Manager Package Setup Configuration

This module configures the package setup for the Book Manager project, which is a tool designed to
manage book projects, analyze content, and generate compilations. It handles all package dependencies,
metadata, and installation configurations.
"""

import os
from typing import List
from setuptools import setup, find_packages


def read_requirements(filename: str = "requirements.txt") -> List[str]:
    """
    Read and parse requirements from a requirements file.

    Args:
        filename (str): Path to the requirements file. Defaults to 'requirements.txt'.

    Returns:
        List[str]: List of requirement specifications.

    Raises:
        FileNotFoundError: If the requirements file doesn't exist.
    """
    if not os.path.exists(filename):
        return []

    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


# Development dependencies
DEV_REQUIRES = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "pylint>=2.15.0",
    "build>=0.10.0",
    "twine>=4.0.0",
    "setuptools>=45",
    "setuptools_scm>=6.2",
    "wheel>=0.37.0",
    "psutil>=5.9.0",
]

# Test dependencies
TEST_REQUIRES = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "psutil>=5.9.0",
]

# Read long description from README
with open("README.md", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

# Parse installation requirements
INSTALL_REQUIRES = read_requirements()

setup(
    name="book_manager",
    author="Wyatt Roersma",
    author_email="wyattroersma@gmail.com",
    description="A tool to manage book projects, analyze content, and generate compilations",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/ThreatFlux/BookManager",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    # Version management
    setup_requires=["setuptools_scm"],
    use_scm_version={
        "write_to": "book_manager/_version.py",
    },
    # Dependencies
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "dev": DEV_REQUIRES,
        "test": TEST_REQUIRES,
    },
    # Console scripts
    entry_points={
        "console_scripts": [
            "book_manager=book_manager.main:main",
        ],
    },
    # Package metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
