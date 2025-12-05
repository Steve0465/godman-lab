# Repository Structure

## Overview

This repository has been refactored into a clean automation lab structure with the following organization:

```
godman-lab/
├── cli/                          # Command-line interface
│   ├── godman/                   # Main CLI package
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point with Typer app
│   │   └── commands/            # CLI command modules
│   │       ├── __init__.py
│   │       └── receipts.py      # Receipt processing commands
│   └── pyproject.toml           # CLI package configuration
│
├── libs/                         # Shared library modules
│   ├── __init__.py
│   ├── receipts.py              # Receipt processing logic
│   ├── expenses.py              # Expense tracking logic
│   └── ocr.py                   # OCR utilities
│
├── apps-script/                  # Google Apps Script automation
│   └── sheets/                   # Spreadsheet automations
│
├── workflows/                    # Automation workflows
│
├── docs/                         # Documentation
├── scans/                        # Input: scanned documents
├── receipts/                     # Output: organized receipts
└── organized_documents/          # Output: organized documents
```

## CLI Usage

### Installation

Install the CLI in development mode:

```bash
cd cli
pip install -e .
```

### Commands

```bash
# Show version
godman version

# Show status
godman status

# Process receipts
godman receipts process --input scans --output receipts

# Show receipt statistics
godman receipts status
```

## Library Modules

### libs/receipts.py
Receipt processing with OCR and AI extraction.

### libs/expenses.py
Expense tracking and summary generation.

### libs/ocr.py
Reusable OCR utilities for images and PDFs.

## Migration Notes

- Original scripts remain in root for backward compatibility
- New code should use the CLI or import from `libs/`
- All functionality preserved, just reorganized
