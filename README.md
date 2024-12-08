# BookManager

[![Tests](https://github.com/ThreatFlux/BookManager/workflows/Tests/badge.svg)](https://github.com/ThreatFlux/BookManager/actions)
[![Lint](https://github.com/ThreatFlux/BookManager/workflows/Lint/badge.svg)](https://github.com/ThreatFlux/BookManager/actions)
[![codecov](https://codecov.io/gh/ThreatFlux/BookManager/branch/main/graph/badge.svg)](https://codecov.io/gh/ThreatFlux/BookManager)
[![PyPI version](https://badge.fury.io/py/book-manager.svg)](https://badge.fury.io/py/book-manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive command-line tool for managing book projects, analyzing content, and generating manuscript compilations in multiple formats.

## Features

- 📂 Automated directory structure scanning and management
- 📊 Scene analysis including:
  - Word counting
  - Term frequency analysis
  - TODO extraction and tracking
- 📚 Manuscript compilation (DOCX, EPUB, PDF*)
- 📈 Progress tracking and reporting
- ⚡ Performance optimized with caching
- 🔍 Detailed error handling and logging

*PDF compilation requires TeXLive/XeLaTeX

## Prerequisites

- Python 3.6 or higher
- Pandoc 2.x or higher (for manuscript compilation)
- For PDF output: TeXLive with XeLaTeX

### Installing Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3-pip pandoc
# Optional - for PDF support:
sudo apt install texlive-xetex
```

#### macOS
```bash
brew install python pandoc
# Optional - for PDF support:
brew install basictex
```

#### Windows
```bash
choco install python pandoc
# Optional - for PDF support:
choco install miktex
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/book_manager.git
cd book_manager
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

## Quick Start

1. Initialize your book project structure:
```bash
mkdir my_book
cd my_book
book_manager --init
```

2. Add your content to the `4_Scenes_and_Chapters/Drafts` directory following this structure:
```
4_Scenes_and_Chapters/
└── Drafts/
    └── Book1/
        └── Act1/
            ├── Scene01.md
            └── Scene02.md
```

3. Run the analysis and compilation:
```bash
book_manager
```

## Usage

### Basic Commands

```bash
# Generate outline only
book_manager --report-only

# Skip compilation
book_manager --no-compile

# Specify output formats
book_manager --output-format docx,epub

# Force reanalysis of all scenes
book_manager --force

# Verbose output
book_manager --verbose
```

### Configuration

Create or modify `config.yaml` in your project root:

```yaml
stopwords:
  - the
  - and
  # Add more stopwords
top_words_count: 5
pandoc_output_formats: [docx, epub]
outline_file: "3_Plot_and_Outline/outline.md"
drafts_dir: "4_Scenes_and_Chapters/Drafts"
compiled_dir: "Compiled"
cache_size: 1000
max_file_size: 10485760  # 10MB
encoding: utf-8
```

### Project Structure

```
my_book/
├── 3_Plot_and_Outline/
│   └── outline.md          # Generated outline
├── 4_Scenes_and_Chapters/
│   └── Drafts/            # Your markdown files
├── Compiled/              # Output files
├── config.yaml            # Configuration
└── .book_manager/         # Cache directory
```

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ThreatFlux/BookManager.git
cd book_manager

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=book_manager

# Run performance tests
pytest tests/test_performance.py
```

## Troubleshooting

### Common Issues

1. **PDF Compilation Failed**
   - Ensure XeLaTeX is installed
   - Check TeXLive installation

2. **Pandoc Not Found**
   - Verify Pandoc installation
   - Ensure Pandoc is in system PATH

3. **Cache Issues**
   - Clear cache: `rm -rf .book_manager/cache`
   - Use `--force` flag to bypass cache

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Authors

- **Wyatt Roersma** - *Project Lead* - [GitHub](https://github.com/wroersma)
- See [AUTHORS.md](AUTHORS.md) for additional contributors

## Acknowledgments

- Inspired by various manuscript management tools
- Built with Python, Pandoc, and other open-source technologies
- Special thanks to all contributors

## Version History

See [CHANGELOG.md](CHANGELOG.md) for all changes.

---

Made with ❤️ by the Book Manager team
