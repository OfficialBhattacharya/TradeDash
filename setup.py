from setuptools import setup, find_packages

setup(
    name="tradedash",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'pandas>=2.2.0',
        'PyQt5>=5.15.0',
        'matplotlib>=3.10.0',
        'yfinance>=0.2.55',
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A professional trading application with real-time stock data visualization",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tradedash",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
) 