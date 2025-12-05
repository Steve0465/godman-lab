# Model Configuration Guide

Learn how to configure, manage, and use both cloud and local language models in GodmanAI.

---

## Overview

GodmanAI supports two model paradigms:

1. **Cloud Models** - OpenAI, Anthropic, Google (API-based)
2. **Local Models** - llama.cpp, GGUF files (run on your machine)

The **Model Router** intelligently selects the best model based on task type, availability, and your preferences.

---

## Cloud Models

### Supported Providers

#### OpenAI
- `gpt-4` - Best reasoning, complex planning
- `gpt-4o` - Faster, multimodal
- `gpt-4o-mini` - Lightweight, cost-effective
- `gpt-4-vision` - Image understanding (deprecated, use gpt-4o)

#### Anthropic (Future)
- `claude-3-opus`
- `claude-3-sonnet`

#### Google (Future)
- `gemini-pro`
- `gemini-pro-vision`

### Configuration

Set your API key:

```bash
# Environment variable
export OPENAI_API_KEY="sk-..."

# Or in .env file
echo "OPENAI_API_KEY=sk-..." >> .env
```

### Usage

Models are automatically selected by the router, but you can force a specific model:

```bash
# Use specific cloud model
godman models run "Explain quantum physics" --model gpt-4

# Use lightweight model
godman models run "Summarize this text" --model gpt-4o-mini
```

### Cost Optimization

**Automatic Selection**:
- Simple tasks → `gpt-4o-mini` (cheapest)
- Complex reasoning → `gpt-4` (most expensive)
- Vision tasks → `gpt-4o` (multimodal)

**Manual Control**:
```python
# In your tool/agent code
from godman_ai.os_core.model_router import ModelRouter

router = ModelRouter()
response = router.run(
    prompt="Your prompt",
    model="gpt-4o-mini",  # Force cheaper model
    max_tokens=100        # Limit output length
)
```

---

## Local Models

### Why Local Models?

- **Privacy** - Data never leaves your machine
- **Cost** - No API fees
- **Speed** - No network latency for small models
- **Offline** - Work without internet

### Supported Formats

GodmanAI uses **llama.cpp** for local inference, supporting:
- GGUF files (recommended)
- GGML files (legacy)

Popular models:
- Llama 2 (7B, 13B, 70B)
- Mistral (7B)
- Mixtral (8x7B)
- Phi-2 (2.7B)
- TinyLlama (1.1B)

---

## Setting Up Local Models

### Step 1: Install llama.cpp

```bash
# macOS
brew install llama.cpp

# Or build from source
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Install Python bindings
pip install llama-cpp-python
```

### Step 2: Download Models

#### Option A: Hugging Face

```bash
# Create models directory
mkdir -p ~/.godman/models

# Download Llama 2 7B (GGUF)
curl -L -o ~/.godman/models/llama-2-7b.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf

# Or use GodmanAI helper
godman models download llama-2-7b
```

#### Option B: Manual Download

Visit these repositories:
- [TheBloke on Hugging Face](https://huggingface.co/TheBloke) - Quantized models
- [Llama](https://huggingface.co/meta-llama) - Official Meta models

Download `.gguf` files to `~/.godman/models/`

### Step 3: Configure Model Directory

```bash
# Set environment variable
export LOCAL_MODEL_DIR="$HOME/.godman/models"

# Or in .env
echo "LOCAL_MODEL_DIR=$HOME/.godman/models" >> .env
```

### Step 4: Verify Installation

```bash
# List available models
godman models list

# Expected output:
# Local Models:
#   - llama-2-7b.Q4_K_M.gguf (7B parameters, 4.2 GB)
#   - mistral-7b-instruct.Q4_K_M.gguf (7B parameters, 4.1 GB)
```

---

## Model Router Configuration

### Router Preferences

Configure via environment variables or settings:

```bash
# Prefer local models over cloud
export PREFER_LOCAL_MODELS=true

# Fallback to cloud if local fails
export FALLBACK_TO_CLOUD=true

# Default local model
export DEFAULT_LOCAL_MODEL="llama-2-7b.Q4_K_M.gguf"
```

Or in Python:

```python
from godman_ai.config import Settings

settings = Settings(
    prefer_local_models=True,
    fallback_to_cloud=True,
    default_local_model="llama-2-7b.Q4_K_M.gguf"
)
```

### Routing Rules

The router selects models based on task type:

| Task Type | Cloud Model | Local Model |
|-----------|-------------|-------------|
| Text analysis | gpt-4o-mini | llama-2-7b |
| Planning | gpt-4 | mistral-7b-instruct |
| Summarization | gpt-4o-mini | llama-2-7b |
| Vision | gpt-4o | llava (future) |
| Code generation | gpt-4 | codellama (future) |

**Fallback Logic**:
1. Check if preferred model type (local/cloud) is available
2. If unavailable, fallback to alternative
3. If both unavailable, return error

---

## Using Models

### CLI Usage

```bash
# Automatic routing (router decides)
godman agent "Summarize this document"

# Force cloud model
godman models run "Complex reasoning task" --model gpt-4

# Force local model
godman models run "Simple text analysis" --model llama-2-7b
```

### Programmatic Usage

```python
from godman_ai.os_core.model_router import ModelRouter

router = ModelRouter()

# Let router decide
response = router.run(
    prompt="Explain quantum computing in simple terms",
    task_type="text_analysis"  # Hints at complexity
)

# Force specific model
response = router.run(
    prompt="What is 2+2?",
    model="llama-2-7b.Q4_K_M.gguf"
)

# Response structure
{
    "model": "llama-2-7b.Q4_K_M.gguf",
    "text": "Quantum computing is...",
    "tokens": 156,
    "duration_ms": 423
}
```

---

## Model Management

### List Models

```bash
godman models list

# Output:
# Cloud Models (OpenAI):
#   - gpt-4 (available)
#   - gpt-4o (available)
#   - gpt-4o-mini (available)
#
# Local Models:
#   - llama-2-7b.Q4_K_M.gguf (7B, 4.2 GB)
#   - mistral-7b-instruct.Q4_K_M.gguf (7B, 4.1 GB)
```

### Download Model

```bash
# Download from Hugging Face
godman models download llama-2-7b

# Specify quantization
godman models download mistral-7b --quant Q4_K_M
```

### Remove Model

```bash
# Delete local model file
rm ~/.godman/models/old-model.gguf

# Or via CLI (future)
godman models remove old-model.gguf
```

### Model Info

```bash
# Get model metadata
godman models info llama-2-7b.Q4_K_M.gguf

# Output:
# Name: llama-2-7b.Q4_K_M.gguf
# Size: 4.2 GB
# Parameters: 7B
# Quantization: Q4_K_M
# Context length: 4096 tokens
# Architecture: llama
```

---

## Quantization Explained

GGUF models come in different quantization levels, trading quality for size/speed:

| Quantization | Size | Quality | Speed | Use Case |
|--------------|------|---------|-------|----------|
| Q2_K | Smallest | Lowest | Fastest | Testing only |
| Q3_K_M | Small | Low | Fast | Simple tasks |
| Q4_K_M | **Medium** | **Good** | **Balanced** | **Recommended** |
| Q5_K_M | Large | High | Slower | Quality-focused |
| Q6_K | Larger | Higher | Slow | Near-original |
| Q8_0 | Largest | Highest | Slowest | Max quality |

**Recommendation**: Start with `Q4_K_M` for best balance.

---

## Performance Tuning

### Hardware Acceleration

#### Metal (Apple Silicon)
```bash
# Install with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python

# Verify Metal is active
godman models info llama-2-7b | grep "Acceleration"
# Should show: "Metal GPU acceleration: enabled"
```

#### CUDA (NVIDIA GPU)
```bash
# Install with CUDA support
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python

# Specify GPU layers
export LLAMA_CUDA_LAYERS=35  # Offload 35 layers to GPU
```

#### CPU Optimization
```bash
# Use all CPU cores
export OMP_NUM_THREADS=$(nproc)

# Enable AVX2/AVX512
CMAKE_ARGS="-DLLAMA_AVX2=on" pip install llama-cpp-python
```

### Context Length

Larger context = more memory:

```python
router.run(
    prompt="...",
    model="llama-2-7b",
    n_ctx=2048  # Context window (default: 512)
)
```

Typical limits:
- Llama 2: 4096 tokens
- Mistral: 8192 tokens
- Mixtral: 32k tokens

### Batch Size

```python
# Process multiple prompts at once
responses = router.batch_run(
    prompts=["Prompt 1", "Prompt 2", "Prompt 3"],
    model="llama-2-7b",
    batch_size=3
)
```

---

## Advanced Configuration

### Custom Model Paths

```python
from godman_ai.os_core.model_router import ModelRouter

router = ModelRouter()
router.register_model(
    name="custom-model",
    path="/path/to/custom-model.gguf",
    priority=10  # Higher = preferred
)
```

### Model Aliases

```bash
# Create alias for long model names
export MODEL_ALIAS_FAST="llama-2-7b.Q4_K_M.gguf"
export MODEL_ALIAS_SMART="mistral-7b-instruct.Q4_K_M.gguf"

# Use alias
godman models run "Question" --model fast
```

### Temperature & Sampling

```python
router.run(
    prompt="Generate creative text",
    model="llama-2-7b",
    temperature=0.8,  # Higher = more creative (0.0 - 2.0)
    top_p=0.95,       # Nucleus sampling
    top_k=40,         # Top-k sampling
    repeat_penalty=1.1
)
```

---

## Multi-Model Workflows

### Ensemble Voting

```python
from godman_ai.os_core.model_router import ModelRouter

router = ModelRouter()

# Ask multiple models
responses = [
    router.run("Is this email spam?", model="gpt-4o-mini"),
    router.run("Is this email spam?", model="llama-2-7b"),
    router.run("Is this email spam?", model="mistral-7b")
]

# Vote on answer
votes = [r["text"] for r in responses]
final_answer = max(set(votes), key=votes.count)
```

### Fast-then-Slow Pattern

```python
# Try fast local model first
result = router.run("Analyze this", model="llama-2-7b")

# If low confidence, use better cloud model
if result.get("confidence", 1.0) < 0.7:
    result = router.run("Analyze this", model="gpt-4")
```

### Specialized Routing

```python
class CustomRouter(ModelRouter):
    def choose_model(self, task_type):
        if task_type == "legal":
            return "gpt-4"  # Use best for legal
        elif task_type == "receipts":
            return "llama-2-7b"  # Local is fine
        else:
            return super().choose_model(task_type)
```

---

## Troubleshooting

### Model Not Found
```bash
# Check model directory
ls -lh $LOCAL_MODEL_DIR

# Verify path in settings
godman os state | grep model_dir
```

### Out of Memory
```bash
# Use smaller quantization
godman models download llama-2-7b --quant Q3_K_M

# Or reduce context length
export DEFAULT_CONTEXT_LENGTH=512
```

### Slow Inference
```bash
# Enable GPU acceleration (if available)
CMAKE_ARGS="-DLLAMA_METAL=on" pip install --upgrade llama-cpp-python

# Use smaller model
godman models download tinyllama-1.1b
```

### API Rate Limits
```bash
# Prefer local models to avoid rate limits
export PREFER_LOCAL_MODELS=true

# Or implement retry logic in your tool
```

---

## Best Practices

### 1. Match Model to Task
- Simple tasks → small local models
- Complex reasoning → cloud models
- Privacy-sensitive → local only

### 2. Cache Results
```python
# Store expensive model outputs
from godman_ai.memory import EpisodicMemory

memory = EpisodicMemory()
cached = memory.recall("similar query")
if cached:
    return cached["result"]
```

### 3. Set Reasonable Limits
```python
router.run(
    prompt="...",
    max_tokens=256,  # Limit response length
    timeout=10       # Timeout after 10s
)
```

### 4. Monitor Costs
```bash
# Track cloud API usage
godman health | grep "api_calls"

# Shows per-model breakdown and estimated cost
```

### 5. Keep Models Updated
```bash
# Check for newer quantizations
godman models check-updates

# Download improved version
godman models download llama-2-7b --quant Q4_K_M --force
```

---

## Model Comparison

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| TinyLlama-1.1B | 0.6 GB | Very Fast | Basic | Simple tasks, testing |
| Llama-2-7B-Q4 | 4.2 GB | Fast | Good | General purpose |
| Mistral-7B-Q4 | 4.1 GB | Fast | Better | Instruction-following |
| Llama-2-13B-Q4 | 7.3 GB | Medium | Great | Complex tasks |
| Mixtral-8x7B-Q4 | 25 GB | Slow | Excellent | Near-GPT-4 quality |
| gpt-4o-mini | Cloud | Fast | Great | Best value cloud |
| gpt-4 | Cloud | Medium | Best | Complex reasoning |

---

## Example Workflows

### Privacy-First Receipt Processing
```bash
# Use local models exclusively
export PREFER_LOCAL_MODELS=true
export FALLBACK_TO_CLOUD=false

godman agent "Process receipts in scans/" --model llama-2-7b
```

### Cost-Optimized Automation
```bash
# Use cheapest models for bulk tasks
godman schedule add "0 9 * * *" "godman agent 'Daily summary' --model gpt-4o-mini"
```

### Hybrid Approach
```python
# Fast local screening, cloud for validation
def process_document(doc_path):
    # Quick local analysis
    quick_result = router.run(f"Is {doc_path} important?", model="llama-2-7b")
    
    if "yes" in quick_result["text"].lower():
        # Deep analysis with cloud model
        return router.run(f"Detailed analysis of {doc_path}", model="gpt-4")
    else:
        return quick_result
```

---

## Next Steps

- [Operations Guide](operations.md) - Deploy models in production
- [Skills Development](skills.md) - Use models in custom tools
- [Architecture](architecture.md) - Understand model routing internals
