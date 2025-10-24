"""
Setup script for PacketClaude
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="packetclaude",
    version="0.1.0",
    description="AX.25 Packet Radio Gateway for Claude AI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="PacketClaude Contributors",
    url="https://github.com/yourusername/packetclaude",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.39.0",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "aiofiles>=23.2.1",
        "structlog>=24.1.0",
    ],
    entry_points={
        "console_scripts": [
            "packetclaude=packetclaude.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Ham Radio",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
