"""
Ring MCP - Setup Configuration

This file contains the package configuration for the Ring MCP server.
"""
import os
from pathlib import Path
from setuptools import setup, find_packages

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements from requirements.txt
def read_requirements():
    requirements = []
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    return requirements

setup(
    name="ring-mcp",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Ring MCP - Universal Control for Ring Devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ring-mcp",
    packages=find_packages(include=['ring_mcp', 'ring_mcp.*']),
    package_data={
        "ring_mcp": ["*.json", "*.yaml", "*.yml"],
    },
    entry_points={
        "console_scripts": [
            "ring-mcp=ring_mcp.__main__:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.15.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "mypy>=0.900",
            "types-python-dateutil>=2.8.0",
            "types-requests>=2.25.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5.0",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ring-mcp/issues",
        "Source": "https://github.com/yourusername/ring-mcp",
    },
)
