#!/usr/bin/env python3
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="mac-calendar-exporter",
    version="0.1.0",
    author="mac-calendar-exporter Team",
    author_email="your-email@example.com",
    description="Export calendar events from macOS Calendar to ICS and upload to SFTP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nodomain/mac-calendar-exporter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Scheduling",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mac-calendar-exporter=caldav_exporter.cli:main",
        ],
    },
)
