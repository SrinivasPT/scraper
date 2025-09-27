# RegScraper

A Python library for scraping regulatory content from web documents including PDF, DOCX, and HTML files. The library provides intelligent downloading capabilities with browser automation support and content extraction with OCR fallback.

## Features

- **Multiple Download Methods**: HTTP client and Playwright browser automation
- **Content Extraction**: Support for PDF, DOCX, and HTML documents
- **OCR Support**: Automatic OCR fallback for scanned documents
- **Robots.txt Compliance**: Respects website crawling policies
- **Request Throttling**: Configurable delays to avoid overwhelming servers
- **CLI Interface**: Command-line tool for quick document scraping
- **Async Support**: Built with async/await for efficient processing

## Installation

Install the package in development mode:

```bash
py -m pip install -e .
```

Install development dependencies:

```bash
py -m pip install -e . ruff pytest pytest-asyncio pytest-cov
```

## Usage

### Command Line Interface

The package can be run as a module with a full command-line interface:

```bash
# Basic usage
py -m regscraper "https://example.com/document.pdf"

# JSON output format
py -m regscraper "https://example.com/document.pdf" --format json

# Save output to file
py -m regscraper "https://example.com/document.pdf" --save output.txt

# JSON output saved to file
py -m regscraper "https://example.com/document.pdf" --format json --save output.json

# Add delay between requests
py -m regscraper "https://example.com/document.pdf" --delay 2

# Quiet mode (suppress logging)
py -m regscraper "https://example.com/document.pdf" --quiet
```

#### CLI Options

- `url`: The URL to scrape (required)
- `--format`: Output format: 'text' (default) or 'json'
- `--save`: Save output to specified file
- `--delay`: Delay between requests in seconds (default: 1)
- `--quiet`: Suppress logging output

### Library Usage

Use the library programmatically in your Python code:

```python
import asyncio
from regscraper.downloader.factory import DownloaderFactory
from regscraper.extractor.factory import ExtractorFactory
from regscraper.infrastructure.robots import RobotsChecker
from regscraper.infrastructure.throttle import RequestThrottler

async def scrape_document(url: str):
    # Initialize components
    robots_checker = RobotsChecker()
    throttler = RequestThrottler(delay=1.0)

    try:
        # Check robots.txt compliance
        can_fetch = await robots_checker.can_fetch(url)
        if not can_fetch:
            print(f"Robots.txt disallows fetching: {url}")
            return

        # Apply throttling
        await throttler.wait()

        # Download content
        downloader = DownloaderFactory.create_downloader("http")
        download_result = await downloader.download(url)

        # Extract content
        extractor = ExtractorFactory.create_extractor(download_result.content_type)
        extraction_result = await extractor.extract(download_result.content)

        print(f"Extracted {len(extraction_result.text)} characters")
        print(extraction_result.text[:500] + "..." if len(extraction_result.text) > 500 else extraction_result.text)

    except Exception as e:
        print(f"Error processing {url}: {e}")

# Run the scraper
asyncio.run(scrape_document("https://example.com/document.pdf"))
```

### Example Script

Run the included example script:

```bash
py example_usage.py
```

## Architecture

The library is organized into several key modules:

### Downloader Module (`regscraper.downloader`)
- **HTTPDownloader**: Fast HTTP client using httpx
- **PlaywrightDownloader**: Browser automation for JavaScript-heavy sites
- **DownloaderFactory**: Factory pattern for creating appropriate downloaders

### Extractor Module (`regscraper.extractor`)
- **PDFExtractor**: Extract text from PDF files with OCR fallback
- **DOCXExtractor**: Extract text from Word documents
- **HTMLExtractor**: Extract clean text from HTML using trafilatura
- **ExtractorFactory**: Factory pattern for content type-specific extraction

### Infrastructure Module (`regscraper.infrastructure`)
- **RobotsChecker**: Validates robots.txt compliance
- **RequestThrottler**: Manages request delays
- **DomainValidator**: URL validation utilities

## Dependencies

Core dependencies:
- `httpx`: Async HTTP client
- `playwright`: Browser automation
- `trafilatura`: HTML content extraction
- `PyMuPDF`: PDF processing
- `python-docx`: DOCX file handling
- `pytesseract`: OCR capabilities
- `pydantic`: Data validation
- `tenacity`: Retry logic
- `aiosqlite`: Async database operations

## Development

### Running Tests

```bash
# Run all tests
py -m pytest tests/ -v

# Run with coverage
py -m pytest tests/ -v --cov=regscraper --cov-report=html --cov-report=term
```

### Code Quality

```bash
# Format code
py -m ruff format src/ tests/

# Lint code
py -m ruff check src/ tests/

# Fix linting issues
py -m ruff check --fix src/ tests/
```

### Available Tasks

The project includes VS Code tasks for common operations:

- **Python: Install Dev Dependencies**: Install all development dependencies
- **Ruff: Format Code**: Format source code
- **Ruff: Lint Code**: Check for linting issues
- **Ruff: Fix Issues**: Automatically fix linting issues
- **Python: Run Tests**: Execute test suite
- **Python: Run Tests with Coverage**: Run tests with coverage reporting
- **Clean: Cache Directories**: Remove Python cache directories

## Example Output

### Text Format
```
Downloaded 462,369 bytes from https://www.sec.gov/files/rules/concept/2025/33-11391.pdf
Extracted 99,968 characters from PDF content

SECURITIES AND EXCHANGE COMMISSION
17 CFR Parts 229, 230, 239, 240, and 249
[Release Nos. 33-11391; 34-104102; File No. S7-2025-04]
...
```

### JSON Format
```json
{
  "url": "https://www.sec.gov/files/rules/concept/2025/33-11391.pdf",
  "content_type": "application/pdf",
  "text": "SECURITIES AND EXCHANGE COMMISSION...",
  "metadata": {
    "pages_processed": 46,
    "ocr_pages": 0
  },
  "length": 99968
}
```

## Error Handling

The library includes comprehensive error handling for:
- Network connectivity issues
- Invalid URLs or unreachable content
- Unsupported file formats
- OCR processing failures
- Robots.txt violations

## License

This project is open source. Please check the license file for details.
