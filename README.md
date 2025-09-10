# Cheque OCR System

A comprehensive solution for extracting structured data from cheque images using PaddleOCR and Streamlit.

![Cheque OCR](https://img.shields.io/badge/Cheque-OCR-blue)
![PaddleOCR](https://img.shields.io/badge/Paddle-OCR-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Interface-green)

## Features

- **Advanced Field Extraction**: Extract payee names, amounts, and dates with high accuracy
- **Cross-Validation**: Validate numerical and written amounts, detect inconsistencies
- **User-Friendly Interface**: Interactive Streamlit web app for easy usage
- **Batch Processing**: Process multiple cheque images at once
- **Detailed Analytics**: View confidence scores, extraction methods, and validation errors
- **Export Options**: Download results as CSV files

## Installation

### Prerequisites

- Python 3.7+
- PaddlePaddle (CPU or GPU version)
- OpenCV

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cheque-ocr.git
   cd cheque-ocr
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Streamlit:
   ```bash
   pip install streamlit
   ```

## Usage

### Streamlit Web Interface

The easiest way to use the Cheque OCR system is through the Streamlit web interface:

```bash
streamlit run app.py
```

This will start a local web server and open the application in your default web browser.

#### Single Image Processing

1. Upload a cheque image using the file uploader
2. The system will automatically process the image and display the extracted information
3. View confidence scores and extraction methods (optional)
4. Download the results as a CSV file

#### Batch Processing

1. Scroll down to the "Batch Processing" section
2. Upload multiple cheque images
3. Click "Process Batch" to start processing
4. View the batch results table
5. Download all results as a CSV file

### Testing

To test the core functionality without Streamlit:

```bash
python test_app.py
```

This will create a sample cheque image and process it using the OCR pipeline.

## System Architecture

### Core Components

- **Image Processor**: Enhances image quality for better OCR results
- **OCR Engine**: Extracts text from images using PaddleOCR
- **Field Extractors**: Specialized modules for each field type
  - **Payee Extractor**: Identifies person and business names
  - **Amount Validator**: Cross-validates numerical and written amounts
  - **Date Normalizer**: Handles multiple date formats
  - **Cheque Number Extractor**: Recognizes various number formats
- **Integrated Field Processor**: Orchestrates the extraction process
- **Streamlit Interface**: User-friendly web application

## Configuration

The system can be configured through the `config/default.ini` file, which includes settings for:

- OCR engine parameters
- Processing options
- Output formatting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) for the OCR engine
- [Streamlit](https://streamlit.io/) for the web interface framework
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing and development)
pip install -r requirements-dev.txt

# Or install the package in development mode
pip install -e .
```

## Usage

### Command Line Usage (Deprecated)
The CLI is no longer maintained. Please use the Streamlit web interface instead:
```bash
streamlit run app.py
```

### Python API Usage
Python API access to batch processors and data models has been deprecated in favor of the Streamlit UI.

## Configuration

The system uses INI configuration files located in the `config/` directory:

- `default.ini` - Default settings
- `development.ini` - Development settings with debug logging
- `production.ini` - Production settings with optimized performance

Key configuration sections:
- `[ocr_settings]` - PaddleOCR configuration
- `[processing]` - Processing parameters and thresholds
- `[output]` - CSV output formatting options
- `[logging]` - Logging configuration

## Output Format

The system extracts the following fields and outputs them to CSV:

| Field | Description | Example |
|-------|-------------|---------|
| payee_name | Name of payment recipient | John Doe |
| amount | Numerical amount | 1500.00 |
| date | Payment date (YYYY-MM-DD) | 2025-01-09 |
| confidence_score | Overall extraction confidence (0.0-1.0) | 0.95 |
| image_filename | Source image file | cheque_001.jpg |

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/cheque_ocr --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

## Development

### Code Standards
- Python 3.8+ with PEP 8 compliance
- Type hints required for all public methods
- Structured logging (no print statements)
- 90% test coverage requirement

### Project Structure
```
cheque-ocr-system/
├── src/cheque_ocr/           # Main package
│   ├── core/                 # Core processing components
│   ├── models/               # Data models
│   ├── processors/           # Processing orchestration
│   ├── interfaces/           # User interfaces
│   └── utils/                # Utilities
├── tests/                    # Test suite
├── config/                   # Configuration files
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
