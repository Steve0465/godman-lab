# Vision AI Setup Guide - GPT-4V & Claude

Quick setup guide for cloud vision AI integration.

## ✅ What's Done

- ✅ VisionAnalyzer class (supports GPT-4V and Claude 3)
- ✅ Integrated into PartIdentifierWorkflow
- ✅ Works for pool parts, receipts, documents, anything!
- ✅ Complete error handling and logging
- ✅ Example scripts

## 🚀 Quick Start (5 minutes)

### 1. Get API Key

**Option A: OpenAI GPT-4V** (recommended for accuracy)
- Go to: https://platform.openai.com/api-keys
- Create API key
- Copy it

**Option B: Anthropic Claude 3** (cheaper, also accurate)
- Go to: https://console.anthropic.com/
- Create API key
- Copy it

### 2. Set Environment Variable

```bash
# For OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# OR for Claude
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Make it permanent (Mac/Linux)
echo 'export OPENAI_API_KEY="sk-your-key"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Test It

```bash
cd ~/Desktop/godman-lab
python examples/vision_analyzer_demo.py
```

## 💻 Usage Examples

### Basic Pool Part Identification

```python
from godman_ai.tools import VisionAnalyzer
from pathlib import Path

# Initialize (uses OpenAI by default)
analyzer = VisionAnalyzer()

# Analyze a pool part
result = analyzer.analyze_pool_part("pump_housing.jpg")

print(f"Part: {result['part_number']}")
print(f"Manufacturer: {result['manufacturer']}")
print(f"Confidence: {result['confidence']:.1%}")
print(f"Alternatives: {result['alternatives']}")
print(f"Equivalents: {result['equivalents']}")
```

### Use Claude Instead

```python
# Use Claude 3 (cheaper, still accurate)
analyzer = VisionAnalyzer(provider="claude")
result = analyzer.analyze_pool_part("image.jpg")
```

### Generic Image Analysis

```python
# Receipt parsing
result = analyzer.analyze(
    "receipt.jpg",
    "Extract vendor, date, total, and items as JSON"
)

# Job documentation
result = analyzer.analyze(
    "job_site.jpg",
    "Describe this pool equipment installation"
)

# Equipment diagnostics
result = analyzer.analyze(
    "broken_pump.jpg",
    "Identify any visible damage or issues"
)
```

### With PartIdentifierWorkflow

```python
import asyncio
from pathlib import Path
from godman_ai.workflows import PartIdentifierWorkflow

async def identify():
    workflow = PartIdentifierWorkflow()
    
    # Uses GPT-4V automatically!
    result = await workflow.identify_part(
        image_path=Path("pool_part.jpg"),
        card_id="trello_card_123"  # Optional: posts to Trello
    )
    
    print(f"Identified: {result['primary_match']['part_number']}")
    if result['is_favorite']:
        print("⭐ This is a favorite part!")
    
    if result['trello_comment']:
        print("✓ Posted to Trello!")

asyncio.run(identify())
```

### Use Claude with Workflow

```python
# Tell workflow to use Claude instead
result = await workflow.identify_part(
    image_path=Path("part.jpg"),
    vision_provider="claude"  # Use Claude instead of OpenAI
)
```

## 💰 Pricing

### OpenAI GPT-4V
- **Low detail**: ~$0.01 per image
- **High detail**: ~$0.03 per image
- Best for: Complex parts, detailed analysis

### Claude 3
- **Haiku**: ~$0.004 per image (fastest, cheapest)
- **Sonnet**: ~$0.012 per image (good balance)
- **Opus**: ~$0.024 per image (best accuracy)
- Best for: Cost-conscious, bulk processing

### Example Monthly Costs

**Light usage** (10 parts/day):
- 300 images/month
- GPT-4V: $3-9/month
- Claude Opus: $7/month
- Claude Sonnet: $3.60/month

**Heavy usage** (50 parts/day):
- 1,500 images/month
- GPT-4V: $15-45/month
- Claude Opus: $36/month
- Claude Sonnet: $18/month

## 🔧 Advanced Configuration

### Custom Model Selection

```python
# Use specific OpenAI model
analyzer = VisionAnalyzer(
    provider="openai",
    model="gpt-4o"  # Latest GPT-4 with vision
)

# Use specific Claude model
analyzer = VisionAnalyzer(
    provider="claude",
    model="claude-3-sonnet-20240229"  # Cheaper, faster
)
```

### Adjust Parameters

```python
result = analyzer.analyze(
    "image.jpg",
    "Your prompt here",
    max_tokens=1500,      # Longer responses
    temperature=0.1       # More deterministic (0.0-1.0)
)
```

### Error Handling

```python
from godman_ai.tools import VisionAnalyzer, VisionError

try:
    analyzer = VisionAnalyzer()
    result = analyzer.analyze_pool_part("image.jpg")
except VisionError as e:
    print(f"Vision analysis failed: {e}")
    # Fall back to manual entry or retry
```

## 🛠️ Troubleshooting

### "Missing OPENAI_API_KEY"
```bash
export OPENAI_API_KEY="your-key-here"
```

### "Missing ANTHROPIC_API_KEY"
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### API Rate Limits
- OpenAI: 500 requests/day (free tier)
- Claude: Check your account limits
- Add retry logic if needed (built-in)

### Image Format Issues
- Supported: JPEG, PNG, WebP
- Max size: 20MB (OpenAI), 5MB (Claude)
- Will automatically base64 encode

### Low Confidence Results
- Try different lighting/angles
- Get closer to part labels
- Ensure part numbers are visible
- Use higher resolution images

## 📊 Performance Tips

**For Best Results:**
1. **Good lighting** - clear, bright photos
2. **Close-ups** - zoom in on part numbers
3. **Multiple angles** - if first result is low confidence
4. **Clean parts** - wipe off dirt/grease for better OCR

**Cost Optimization:**
1. Use Claude Sonnet for bulk processing
2. Switch to GPT-4V only for complex cases
3. Cache common parts (build a database)
4. Batch similar requests

## 🔄 Fallback Strategy

The workflow automatically falls back to mock data if vision fails:

```python
# Vision AI tries first
try:
    result = analyzer.analyze_pool_part(image)
except Exception:
    # Falls back to mock data or manual entry
    # Workflow still completes
```

## 🎯 Next Steps

1. **Set API key** (OpenAI or Claude)
2. **Take test photo** of a pool part
3. **Run identification**: `workflow.identify_part(image_path)`
4. **Check accuracy** - is it good enough?
5. **Adjust** - try different models/providers
6. **Scale up** - use in production!

## 📚 Related Files

- **Code**: `godman_ai/tools/vision.py`
- **Workflow**: `godman_ai/workflows/part_identifier_workflow.py`
- **Demo**: `examples/vision_analyzer_demo.py`
- **Docs**: `PART_IDENTIFIER_TRELLO_README.md`

## 🚢 Ready to Ship!

You now have:
- ✅ Real vision AI (GPT-4V or Claude)
- ✅ Trello integration
- ✅ Favorites management
- ✅ Complete workflow
- ✅ Error handling
- ✅ Fallback support

Just add an API key and you're live! 🎉

---

**Questions?** Check the demo script or ping me! 🚀
