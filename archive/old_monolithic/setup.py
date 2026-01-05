from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="studioflow",
    version="1.0.0",
    author="StudioFlow Contributors",
    description="Professional video project organization made simple",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/studioflow",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "rich>=10.0",
        "pyyaml>=5.4",
        "pathlib",
    ],
    entry_points={
        "console_scripts": [
            "studioflow=studioflow.cli.main:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "studioflow": [
            "templates/*.yml",
            "examples/*.yml",
        ],
    },
)
