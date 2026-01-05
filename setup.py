"""
StudioFlow Setup Configuration
Modern Python packaging with pip installation support
"""

from setuptools import setup, find_packages
from pathlib import Path


# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text()


setup(
    name="studioflow",
    version="2.0.0",
    author="StudioFlow Team",
    author_email="",
    description="Automated video production pipeline with modern CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/studioflow",

    # Package configuration
    packages=find_packages(),
    python_requires=">=3.10",

    # Dependencies
    install_requires=[
        "typer>=0.9.0",
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "ffmpeg-python>=0.2.0",
        "Pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "moviepy>=1.0.3",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "httpx>=0.25.0",
    ],

    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "ruff>=0.0.250",
        ],
        "resolve": [
            # DaVinci Resolve API (if available as package)
        ],
        "youtube": [
            "google-api-python-client>=2.0.0",
            "google-auth-httplib2>=0.1.0",
            "google-auth-oauthlib>=1.0.0",
        ],
        "ai": [
            "openai-whisper>=20231117",
            "torch>=2.0.0",
        ],
    },

    # Entry points for CLI commands
    entry_points={
        "console_scripts": [
            "sf=studioflow.cli.main:run",
            "studioflow=studioflow.cli.main:run",
        ],
    },

    # Package data
    package_data={
        "studioflow": [
            "templates/*",
            "config/*.yaml",
        ],
    },

    # Classifiers for PyPI
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],

    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/yourusername/studioflow/issues",
        "Source": "https://github.com/yourusername/studioflow",
        "Documentation": "https://studioflow.readthedocs.io",
    },
)