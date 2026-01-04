# Measurements OCR Batch Workflow

## Overview

The `MeasurementsOCRBatchWorkflow` is a specialized workflow for extracting pool measurements and customer information from images and PDFs using OCR (Optical Character Recognition).

## Features

- **OCR Integration**: Uses the built-in `OCRTool` to extract text from images and PDFs
- **Intelligent Measurement Parsing**: Recognizes various measurement formats:
  - `20 x 40`
  - `20' x 40'`
  - `20ft x 40ft`
  - `20 by 40`
  - `Pool: 20x40`
- **Customer Name Extraction**: Automatically identifies customer names from labels like:
  - `Customer: John Doe`
  - `Owner: Jane Smith`
  - `Name: Bob Johnson`
- **Validation**: Ensures extracted measurements are reasonable:
  - Minimum dimension: 5 ft
  - Maximum dimension: 200 ft
  - Aspect ratio warnings for unusual shapes (>10:1)
- **Batch Processing**: Process multiple files in a single workflow run
- **Detailed Results**: Returns comprehensive metadata including confidence scores and validation errors

## Usage

### Basic Usage

```python
from godman_ai.engine import AgentEngine

# Initialize the engine
engine = AgentEngine()

# Process files
result = engine.run_workflow(
    'measurements_ocr_batch',
    input_files=['pool_invoice1.pdf', 'pool_invoice2.jpg']
)

# Check results
print(f"Processed: {result['processed']}/{result['total_files']}")

for file_result in result['results']:
    if file_result['is_valid']:
        print(f"File: {file_result['file']}")
        print(f"Customer: {file_result['customer_name']}")
        print(f"Measurements: {file_result['measurements']} ft")
    else:
        print(f"Errors: {file_result['validation_errors']}")
```

### Direct Function Usage

```python
from godman_ai.workflows.measurements_ocr_batch import MeasurementsOCRBatchWorkflow

workflow = MeasurementsOCRBatchWorkflow(engine=None)

# Extract measurements
text = "Pool dimensions: 25 x 50"
measurements, confidence = workflow.extract_measurements(text)
print(f"Measurements: {measurements} (confidence: {confidence})")

# Extract customer name
text = "Customer: John Smith\nPool: 20 x 40"
customer = workflow.extract_customer_name(text)
print(f"Customer: {customer}")

# Validate measurements
errors = workflow.validate_measurements((20.0, 40.0))
if errors:
    print(f"Validation errors: {errors}")
else:
    print("Valid measurements")
```

## OCRResult Structure

Each processed file returns an `OCRResult` object with the following fields:

- `file` (str): Path to the processed file
- `text` (str): Extracted OCR text
- `customer_name` (str|None): Extracted customer name
- `measurements` (tuple|None): Extracted dimensions as (width, height) in feet
- `confidence` (float): Confidence score for measurement extraction (0.0-1.0)
- `validation_errors` (list): List of validation error messages
- `metadata` (dict): Additional metadata (file size, extension, text length)
- `is_valid` (bool): Whether the result has valid extracted data

## Validation Rules

The workflow applies the following validation rules:

1. **Minimum Dimension**: 5.0 ft
   - Pools smaller than this are flagged as invalid

2. **Maximum Dimension**: 200.0 ft
   - Pools larger than this are flagged as invalid

3. **Aspect Ratio**: Max 10:1
   - Unusual aspect ratios generate warnings

## Supported Measurement Formats

The workflow recognizes measurements in various formats:

| Format | Example | Confidence |
|--------|---------|------------|
| `X x Y` | `20 x 40` | High (1.0) |
| `X' x Y'` | `20' x 40'` | High (1.0) |
| `Xft x Yft` | `20ft x 40ft` | High (1.0) |
| `X by Y` | `20 by 40` | Medium (0.9) |
| With label | `Pool: 20 x 40` | High (1.0) |

## Batch Processing

The workflow supports batch processing of multiple files:

```python
result = engine.run_workflow(
    'measurements_ocr_batch',
    input_files=['file1.pdf', 'file2.jpg', 'file3.png']
)

# Access batch statistics
print(f"Total files: {result['total_files']}")
print(f"Successfully processed: {result['processed']}")
print(f"Failed: {result['failed']}")
```

## Error Handling

The workflow handles errors gracefully:

- **File not found**: Returns result with validation error
- **OCR failure**: Returns result with OCR error message
- **No measurements found**: Returns result with None measurements
- **Invalid measurements**: Returns result with validation errors

All errors are captured in the `validation_errors` field of the result.

## Testing

The workflow includes comprehensive tests covering:

- Measurement extraction (various formats)
- Customer name extraction
- Validation logic
- Batch processing
- Error handling
- Integration with the AgentEngine

Run tests with:

```bash
pytest tests/test_measurements_ocr_batch.py -v
```

## Demo

A demonstration script is available to showcase the workflow capabilities:

```bash
python godman_ai/workflows/demo_measurements_ocr.py
```

## Integration with Orchestrator

The workflow is automatically registered with the AgentEngine and can be invoked through:

1. **Direct workflow execution**: `engine.run_workflow('measurements_ocr_batch', ...)`
2. **CLI**: `godman workflow measurements_ocr_batch file1.pdf file2.jpg`
3. **API**: POST to `/workflow/measurements_ocr_batch` endpoint (when service is running)

## Future Enhancements

Potential improvements for the workflow:

- Support for more measurement units (meters, yards)
- Enhanced customer name extraction using NLP
- Integration with pool service database
- Automatic data export to Google Sheets
- Support for handwritten measurements
- Multi-language OCR support
