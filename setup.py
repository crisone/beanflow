from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="beanflow",
    version="0.1.0",
    author="Yuan Jiang",
    author_email="jiangyuan26@gmail.com",
    description="A Python library for Beancount workflow beanflow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/crisone/beanflow",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "beancount",
        "PyYAML>=5.1",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        'console_scripts': [
            'beanflow=beanflow.cli:main',
        ],
    },
) 