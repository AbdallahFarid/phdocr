"""
Cheque OCR System - Extract structured data from cheque images using PaddleOCR.

This package provides a comprehensive solution for processing cheque images
and extracting structured data including payee names, amounts, dates, and cheque numbers.
"""

__version__ = "2.0.0"
__author__ = "Cheque OCR Development Team"

# Minimal exports for Streamlit app
from .utils.config_manager import ConfigManager

__all__ = [
    'ConfigManager',
    '__version__',
    '__author__',
]
