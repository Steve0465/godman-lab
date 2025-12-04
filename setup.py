"""Setup file for enhanced OCR/analysis package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="godman-lab-enhanced",
    version="1.0.0",
    author="Steve0465",
    description="Enhanced OCR/analysis features for screenshot and screen-recording ingestion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Steve0465/godman-lab",
    packages=find_packages(include=['prototype', 'prototype.*', 'webapp', 'webapp.*']),
    python_requires=">=3.9",
    install_requires=[
        "pytesseract>=0.3.10",
        "pillow>=10.0.0",
        "opencv-python>=4.8.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "cloud": [
            "google-cloud-vision>=3.4.0",
            "boto3>=1.28.0",
        ],
        "embeddings": [
            "sentence-transformers>=2.2.2",
            "faiss-cpu>=1.7.4",
            "scikit-learn>=1.3.0",
        ],
        "webapp": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "python-multipart>=0.0.6",
            "aiofiles>=23.2.0",
            "aiosqlite>=0.19.0",
            "streamlit>=1.28.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ],
        "all": [
            "google-cloud-vision>=3.4.0",
            "boto3>=1.28.0",
            "sentence-transformers>=2.2.2",
            "faiss-cpu>=1.7.4",
            "scikit-learn>=1.3.0",
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "python-multipart>=0.0.6",
            "aiofiles>=23.2.0",
            "aiosqlite>=0.19.0",
            "streamlit>=1.28.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        'console_scripts': [
            'ocr-process-folder=prototype.enhanced.process_folder:main',
            'ocr-compare-backends=prototype.enhanced.compare_ocr_backends:main',
            'ocr-demo=prototype.enhanced.demo:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
