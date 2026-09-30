"""
RAG System Package Setup

Installation:
    pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="rag-system",
    version="0.1.0",
    author="RAG System Team",
    description="Retrieval-Augmented Generation for PDF Documents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/rag-system",
    packages=find_packages(exclude=['tests', 'tests_*']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "PyMuPDF>=1.23.0",
        "pdfplumber>=0.10.4",
        "pdf2image>=1.16.3",
        "PyTesseract>=0.3.10",
        "python-tesseract>=0.2.0",
        "chromadb>=0.4.22",
        "Pillow>=10.0.0",
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "sentence-transformers>=2.2.0",
        "numpy>=1.26.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "flake8>=6.1.0",
            "mypy>=1.0.0",
        ],
        "pgvector": [
            "psycopg2-binary>=2.9.0",
        ],
        "weaviate": [
            "weaviate-client>=3.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "rag-system=rag_system.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "rag_system": ["py.typed"],
    },
)