from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="localfindata",
    version="0.1.0",
    packages=find_packages(),
    description="Download financial data with indicators and generate candlestick charts.",
    author="LocalFinData",
    license="MIT",
    python_requires=">=3.10",
    install_requires=[
        "pandas>=1.5",
        "numpy>=1.21",
        "yfinance>=0.2",
        "matplotlib>=3.7",
        "ta>=0.11",
    ],
)
