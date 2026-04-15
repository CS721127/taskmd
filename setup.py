from setuptools import setup, find_packages

setup(
    name="taskmd",
    version="0.2.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "tomli-w>=1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "tm=taskmd.cli:main",
        ],
    },
)
