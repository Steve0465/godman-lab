# Skills Development Guide

Learn how to build, package, and distribute custom tools and agents for GodmanAI.

---

## What is a Skill?

A **skill** is a packaged extension for GodmanAI that adds new capabilities. Skills can contain:
- **Tools** - Single-purpose functions (OCR, image analysis, API integrations)
- **Agents** - Complex multi-step logic with decision-making
- **Workflows** - Pre-defined sequences of tool calls
- **Mixed** - Combination of the above

---

## Skill Lifecycle

```
Create → Develop → Test → Package → Install → Use
```

1. **Create** - Scaffold a new skill from template
2. **Develop** - Write tool/agent logic
3. **Test** - Validate locally
4. **Package** - Build `.godmanskill` archive
5. **Install** - Deploy to GodmanAI
6. **Use** - Call from CLI, API, or agents

---

## Quick Start

### Create a New Skill

```bash
# Scaffold from template
godman skill new invoice-analyzer

# Directory created:
# godman_ai/plugins/invoice-analyzer/
#   __init__.py
#   tool.py
#   agent.py
#   manifest.yaml
```

### Edit the Tool

Edit `godman_ai/plugins/invoice-analyzer/tool.py`:

```python
from godman_ai.engine import BaseTool

class InvoiceAnalyzerTool(BaseTool):
    name = "invoice_analyzer"
    description = "Extracts line items and totals from invoices."
    
    def run(self, **kwargs):
        # Get input
        invoice_path = kwargs.get("invoice_path")
        
        # Your logic here
        # Example: OCR → parse → structure data
        from PIL import Image
        import pytesseract
        
        img = Image.open(invoice_path)
        text = pytesseract.image_to_string(img)
        
        # Parse text (simplified example)
        lines = text.split('\n')
        total = self._extract_total(lines)
        items = self._extract_items(lines)
        
        return {
            "total": total,
            "items": items,
            "raw_text": text
        }
    
    def _extract_total(self, lines):
        for line in lines:
            if "TOTAL" in line.upper():
                # Extract numeric value
                import re
                match = re.search(r'\$?(\d+\.\d{2})', line)
                if match:
                    return float(match.group(1))
        return None
    
    def _extract_items(self, lines):
        # Implement line item extraction
        return []
```

### Update the Manifest

Edit `manifest.yaml`:

```yaml
name: invoice-analyzer
version: 0.1.0
description: Analyzes invoices and extracts line items and totals.
type: tool
entrypoint: tool:InvoiceAnalyzerTool
author: Your Name
tags:
  - invoice
  - ocr
  - documents
requires:
  - pillow
  - pytesseract
```

### Test Locally

```bash
# Test the tool directly
python -c "
from godman_ai.plugins.invoice_analyzer.tool import InvoiceAnalyzerTool
tool = InvoiceAnalyzerTool()
result = tool.run(invoice_path='test_invoice.pdf')
print(result)
"

# Or through the orchestrator
godman run test_invoice.pdf
```

### Package the Skill

```bash
# Create .godmanskill package
godman skill package godman_ai/plugins/invoice-analyzer

# Creates: invoice-analyzer.godmanskill (a zip archive)
```

### Install the Skill

```bash
# Install locally
godman skill install invoice-analyzer.godmanskill

# Or install from the app store
godman store install invoice-analyzer
```

### Use the Skill

```bash
# Direct tool call
godman run invoice.pdf

# Through agent
godman agent "Analyze all invoices in docs/ folder"

# Via API
curl -X POST http://127.0.0.1:8000/run \
  -H "Authorization: Bearer $GODMAN_API_TOKEN" \
  -d '{"input": "invoice.pdf"}'
```

---

## Skill Anatomy

### Directory Structure

```
godman_ai/plugins/my-skill/
    __init__.py          # Empty or imports
    tool.py              # Tool implementation
    agent.py             # Agent implementation (optional)
    manifest.yaml        # Skill metadata
    requirements.txt     # Python dependencies (optional)
    README.md            # Documentation (optional)
    tests/               # Unit tests (optional)
```

### Manifest Format

```yaml
# Required fields
name: my-skill
version: 0.1.0
description: Short description of what this skill does.
type: tool  # or "agent" or "mixed"
entrypoint: tool:MyTool  # or "agent:MyAgent"

# Optional fields
author: Your Name
email: you@example.com
url: https://github.com/you/my-skill
license: MIT
tags:
  - category1
  - category2
requires:
  - pillow>=9.0.0
  - requests
```

**Type Options**:
- `tool` - Single tool class
- `agent` - Single agent class
- `mixed` - Multiple tools/agents

**Entrypoint Format**:
- `module:ClassName` where module is relative to skill root
- Examples: `tool:OCRTool`, `agent:InvoiceAgent`, `utils:HelperTool`

---

## Building Tools

### BaseTool Contract

```python
from godman_ai.engine import BaseTool

class MyTool(BaseTool):
    # Required: unique tool name
    name = "my_tool"
    
    # Required: human-readable description
    description = "What this tool does and when to use it."
    
    # Required: main execution method
    def run(self, **kwargs):
        """
        Process input and return structured output.
        
        Args:
            **kwargs: Flexible input parameters
            
        Returns:
            dict: Structured result
        """
        # Your logic here
        return {"result": "success"}
```

### Input Handling

```python
def run(self, **kwargs):
    # Extract parameters with defaults
    file_path = kwargs.get("file_path")
    mode = kwargs.get("mode", "default")
    
    # Validate inputs
    if not file_path:
        return {"error": "file_path required"}
    
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    # Process...
    return {"result": "..."}
```

### Error Handling

```python
def run(self, **kwargs):
    try:
        # Main logic
        result = self._process(kwargs)
        return {"success": True, "data": result}
    except FileNotFoundError as e:
        return {"success": False, "error": f"File not found: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Lazy Imports

```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "Uses heavy library"
    
    def run(self, **kwargs):
        # Import here, not at module level
        import heavy_library
        
        result = heavy_library.process(kwargs["input"])
        return {"result": result}
```

### Logging

```python
import logging

class MyTool(BaseTool):
    name = "my_tool"
    description = "Example with logging"
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def run(self, **kwargs):
        self.logger.info(f"Processing input: {kwargs}")
        
        # Logic...
        
        self.logger.debug("Intermediate result: ...")
        return {"result": "..."}
```

---

## Building Agents

### Agent Structure

```python
class MyAgent:
    """
    Custom agent for complex multi-step tasks.
    """
    
    def __init__(self, engine=None):
        """
        Args:
            engine: Reference to AgentEngine for calling tools
        """
        self.engine = engine
    
    def run(self, task_input):
        """
        Main execution method.
        
        Args:
            task_input: User's task description or input data
            
        Returns:
            dict: Final result
        """
        # Step 1: Analyze input
        analysis = self._analyze(task_input)
        
        # Step 2: Call tools
        if self.engine:
            ocr_result = self.engine.call_tool("ocr", image_path=task_input)
        else:
            ocr_result = self._run_ocr_directly(task_input)
        
        # Step 3: Process and return
        return self._process(ocr_result)
```

### Using Tools from Agents

```python
def run(self, task_input):
    # Call tool via engine
    ocr_result = self.engine.call_tool("ocr", image_path=task_input)
    
    # Parse result
    text = ocr_result.get("text")
    
    # Call another tool
    parse_result = self.engine.call_tool("parser", text=text)
    
    # Final processing
    return {"data": parse_result}
```

---

## Testing Skills

### Unit Tests

Create `tests/test_tool.py`:

```python
import pytest
from godman_ai.plugins.my_skill.tool import MyTool

def test_tool_basic():
    tool = MyTool()
    result = tool.run(input="test")
    assert result["success"] is True

def test_tool_error_handling():
    tool = MyTool()
    result = tool.run()  # Missing input
    assert result["success"] is False
    assert "error" in result

def test_tool_with_file():
    tool = MyTool()
    result = tool.run(file_path="test_data/sample.txt")
    assert "data" in result
```

Run tests:

```bash
pytest godman_ai/plugins/my-skill/tests/
```

### Integration Tests

Test with orchestrator:

```python
from godman_ai.orchestrator import Orchestrator

def test_integration():
    orchestrator = Orchestrator()
    orchestrator.load_tools_from_package("godman_ai.tools")
    
    result = orchestrator.run_task("test_input.jpg")
    assert result["success"] is True
```

---

## Packaging & Distribution

### Validate Skill

```bash
# Check manifest and structure
godman skill validate godman_ai/plugins/my-skill

# Output:
# ✓ Manifest valid
# ✓ Entrypoint exists
# ✓ BaseTool implemented correctly
# ✓ All required files present
```

### Build Package

```bash
# Create .godmanskill archive
godman skill package godman_ai/plugins/my-skill

# Creates: my-skill.godmanskill
```

### Share Skill

#### Option 1: File-based
```bash
# Send .godmanskill file directly
scp my-skill.godmanskill user@server:/path/

# Install on remote machine
godman skill install my-skill.godmanskill
```

#### Option 2: App Store Registry

Submit to private app store:

1. Add entry to registry:
```json
{
  "name": "my-skill",
  "version": "0.1.0",
  "description": "...",
  "url": "https://example.com/skills/my-skill.godmanskill",
  "tags": ["ocr", "documents"]
}
```

2. Users install via:
```bash
godman store install my-skill
```

---

## Advanced Patterns

### Multi-Tool Skill

```python
# tool1.py
class Tool1(BaseTool):
    name = "tool1"
    def run(self, **kwargs):
        return {"result": "tool1"}

# tool2.py
class Tool2(BaseTool):
    name = "tool2"
    def run(self, **kwargs):
        return {"result": "tool2"}

# manifest.yaml
type: mixed
entrypoints:
  - tool1:Tool1
  - tool2:Tool2
```

### Tool Dependencies

```python
class AdvancedTool(BaseTool):
    name = "advanced"
    
    def __init__(self, orchestrator=None):
        super().__init__()
        self.orchestrator = orchestrator
    
    def run(self, **kwargs):
        # Use another tool
        ocr_result = self.orchestrator.run_task(kwargs["image"])
        
        # Process OCR result
        return self._process(ocr_result)
```

### Configuration

```python
# config.py
import os

class SkillConfig:
    API_KEY = os.getenv("MY_SKILL_API_KEY")
    TIMEOUT = int(os.getenv("MY_SKILL_TIMEOUT", 30))

# tool.py
from .config import SkillConfig

class MyTool(BaseTool):
    def run(self, **kwargs):
        api_key = SkillConfig.API_KEY
        timeout = SkillConfig.TIMEOUT
        # Use config...
```

### External API Integration

```python
class APITool(BaseTool):
    name = "api_tool"
    description = "Calls external API"
    
    def run(self, **kwargs):
        import requests
        
        response = requests.post(
            "https://api.example.com/endpoint",
            json=kwargs,
            timeout=30
        )
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
```

---

## Best Practices

### 1. Keep Tools Focused
- One tool = one responsibility
- Break complex tasks into multiple tools

### 2. Use Lazy Imports
- Import heavy libraries inside `run()`, not at top
- Keeps startup time fast

### 3. Handle Errors Gracefully
- Never let exceptions propagate uncaught
- Return structured error responses

### 4. Document Thoroughly
- Add docstrings to all methods
- Include examples in README.md

### 5. Test Edge Cases
- Missing inputs
- Invalid file formats
- Network failures
- Timeout scenarios

### 6. Version Carefully
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Document breaking changes
- Test upgrades

### 7. Respect Privacy
- Don't send data to external services without user consent
- Log access to sensitive data
- Encrypt credentials

### 8. Optimize Performance
- Cache expensive computations
- Use streaming for large files
- Parallelize when possible

---

## Example Skills

### PDF Extractor

```python
class PDFExtractorTool(BaseTool):
    name = "pdf_extractor"
    description = "Extracts text and metadata from PDFs"
    
    def run(self, **kwargs):
        import pdfplumber
        
        pdf_path = kwargs.get("pdf_path")
        
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages])
            metadata = pdf.metadata
        
        return {
            "text": text,
            "num_pages": len(pdf.pages),
            "metadata": metadata
        }
```

### Email Monitor

```python
class EmailMonitorTool(BaseTool):
    name = "email_monitor"
    description = "Checks inbox for new emails matching criteria"
    
    def run(self, **kwargs):
        import imaplib
        import email
        
        # Connect to inbox
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(kwargs["email"], kwargs["password"])
        mail.select("inbox")
        
        # Search
        _, message_ids = mail.search(None, kwargs.get("query", "ALL"))
        
        # Fetch recent
        messages = []
        for msg_id in message_ids[0].split()[-10:]:
            _, msg_data = mail.fetch(msg_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            messages.append({
                "subject": msg["subject"],
                "from": msg["from"],
                "date": msg["date"]
            })
        
        return {"messages": messages}
```

### Image Classifier

```python
class ImageClassifierTool(BaseTool):
    name = "image_classifier"
    description = "Classifies images using a pre-trained model"
    
    def run(self, **kwargs):
        from PIL import Image
        import torch
        from torchvision import models, transforms
        
        # Load model (cache this in production)
        model = models.resnet50(pretrained=True)
        model.eval()
        
        # Preprocess image
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
        ])
        
        img = Image.open(kwargs["image_path"])
        img_tensor = transform(img).unsqueeze(0)
        
        # Predict
        with torch.no_grad():
            output = model(img_tensor)
        
        # Get top class
        _, predicted = torch.max(output, 1)
        
        return {"class": predicted.item()}
```

---

## Troubleshooting

### Skill Not Loading
```bash
# Check logs
grep "plugin" .godman/logs/godman.log

# Validate structure
godman skill validate godman_ai/plugins/my-skill

# Check manifest syntax
cat godman_ai/plugins/my-skill/manifest.yaml
```

### Import Errors
```python
# Use relative imports within skill
from .utils import helper_function

# Or absolute from skill root
from godman_ai.plugins.my_skill.utils import helper_function
```

### Tool Not Discovered
- Ensure class inherits from `BaseTool`
- Check manifest `entrypoint` matches actual class name
- Verify `__init__.py` exists

---

## Next Steps

- [Operations Guide](operations.md) - Deploy and manage skills in production
- [Model Configuration](models.md) - Use LLMs within your skills
- [Architecture](architecture.md) - Understand how skills integrate with the system
