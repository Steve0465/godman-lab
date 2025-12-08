# 🎮 Fun Tools & Playground - Complete Setup

## 🎉 What We Built

A complete interactive playground for your Godman AI system with exciting prebuilt tools!

---

## 🛠️ Installed Tools

### 1. **figlet** - ASCII Art Text
```bash
figlet "Hello World"
figlet -f banner "GODMAN AI"
```

### 2. **lolcat** - Rainbow Colors
```bash
echo "Rainbow text!" | lolcat
figlet "Colorful" | lolcat
```

### 3. **fx** - Interactive JSON Viewer
```bash
curl -s http://localhost:8000/api/handler/tools | fx
echo '{"name":"test"}' | fx
```

### 4. **btop** - Beautiful System Monitor
```bash
btop  # Real-time CPU, RAM, processes
```

### 5. **jq** - JSON Processor
```bash
curl -s http://localhost:8000/api/presets | jq '.presets[].name'
```

---

## 🎯 Scripts Created

### 1. **fun_demo.py** - Automated Demo
```bash
python3 ~/Desktop/godman-lab/fun_demo.py
```

**Features:**
- Rainbow ASCII banner
- Tests all 5 tool categories
- Pretty JSON output
- Automated execution

**Demo includes:**
- Math operations (add 42 + 58)
- String operations (lowercase HELLO)
- Text manipulation (reverse "Godman AI")
- Data analysis (calculate stats)
- User management (create user Bob)

### 2. **playground.sh** - Interactive Menu
```bash
~/Desktop/godman-lab/playground.sh
```

**Options:**
1. 🎨 View Tools as Beautiful JSON (fx)
2. 📊 System Monitor (btop)
3. 🌈 Create Rainbow Text
4. 🔥 Test All Math Functions
5. 📝 Test All String Functions
6. 📈 Run Stats Analysis
7. 🎪 Hollywood Hacker Mode
8. 🌐 Open WebUI Dashboard
9. 🤖 Interactive Handler Chat
0. 🚪 Exit

### 3. **codex** - AI Model CLI
```bash
codex "your prompt"
codex --overmind "plan a project"
codex --forge "write code"
codex --handler "add 5 and 3"
```

---

## 🤖 AI Models Available

### 1. **DeepSeek-R1:14b** (Overmind)
```bash
ollama run deepseek-r1
codex --overmind "your strategic question"
```
**Use for:** Planning, reasoning, strategy

### 2. **Gorilla OpenFunctions** (Handler)
```bash
ollama run froehnerel/gorilla-openfunctions:v2-q5_K_M
codex --handler "natural language request"
```
**Use for:** Converting language → function calls

### 3. **Qwen2.5-Coder:7b** (Forge)
```bash
ollama run qwen2.5-coder:7b
codex --forge "code generation request"
```
**Use for:** Code generation, implementation

---

## 🎮 Quick Start Guide

### Test the Complete System:

**1. Start the Server:**
```bash
cd ~/Desktop/godman-lab
uvicorn godman_ai.server.api:app --reload
```

**2. Run the Fun Demo:**
```bash
python3 fun_demo.py
```

**3. Try the Playground:**
```bash
./playground.sh
# Choose option 4 or 5 to see tools in action
```

**4. Open the WebUI:**
```bash
open http://localhost:8000
```

**5. Use Handler Model:**
```bash
echo "add 10 and 20" | ollama run froehnerel/gorilla-openfunctions:v2-q5_K_M
```

---

## 🎨 Fun Examples

### Rainbow Banner:
```bash
figlet "GODMAN AI" | lolcat
```

### Test All Math:
```bash
curl -s -X POST http://localhost:8000/api/handler \
  -H "Content-Type: application/json" \
  -d '{"function": "add", "parameters": {"x": 42, "y": 58}}' | jq '.result'
```

### Interactive JSON:
```bash
curl -s http://localhost:8000/api/handler/tools | fx
# Navigate with arrow keys, press 'q' to quit
```

### System Monitor:
```bash
btop
# Beautiful real-time system monitor
```

---

## 📊 Your Tool Arsenal

### 11 Registered Tools:

**Math (3):**
- add(x, y) → sum
- subtract(x, y) → difference
- multiply(x, y) → product

**String (3):**
- uppercase(text) → UPPERCASE
- lowercase(text) → lowercase
- reverse_text(text) → txet

**Data (2):**
- calculate_stats(items) → avg, sum, min, max
- word_count(text) → count

**User (1):**
- create_user(name, age) → user_id, profile

**System (2):**
- list_files(path) → directory contents
- echo(text) → stdout

---

## 🚀 Integration Examples

### Use with WebUI:
1. Open http://localhost:8000
2. Click "List Tools"
3. Enter function name and parameters
4. Click "Run Tool"
5. See formatted JSON output

### Use with CLI:
```bash
# Via codex
codex --handler "add 5 and 3"

# Via direct ollama
echo "create user Alice age 25" | ollama run froehnerel/gorilla-openfunctions:v2-q5_K_M

# Via curl
curl -X POST http://localhost:8000/api/handler \
  -H "Content-Type: application/json" \
  -d '{"function": "add", "parameters": {"x": 5, "y": 3}}'
```

### Use with Python:
```python
import requests

response = requests.post(
    "http://localhost:8000/api/handler",
    json={"function": "add", "parameters": {"x": 5, "y": 3}}
)
print(response.json())
```

---

## 🎯 What Makes This Fun

✅ **Visual** - Rainbow colors, ASCII art, beautiful UI
✅ **Interactive** - Menu-driven, real-time feedback
✅ **Powerful** - Real tools solving real problems
✅ **Educational** - See how APIs work
✅ **Extensible** - Easy to add more tools

---

## 💡 Next Steps

### Add More Tools:
1. Edit `register_tools.py`
2. Add `@tool` decorator
3. Define function with schema
4. Server auto-reloads
5. Tool appears in WebUI

### Create Custom Workflows:
1. Use Overmind to plan
2. Use Forge to implement
3. Use Handler to execute
4. Monitor with btop
5. Debug with fx

### Experiment:
- Try different AI models
- Chain multiple tools
- Build automation scripts
- Create dashboards
- Integrate with other services

---

## 📚 Resources

**Documentation:**
- TOOL_RUNNER_README.md - Tool framework
- HANDLER_API_README.md - API docs
- APP_JS_REFACTOR.md - Frontend docs
- API_ROUTING_UPDATE.md - Routing guide

**Scripts:**
- `codex` - AI model CLI
- `fun_demo.py` - Automated demo
- `playground.sh` - Interactive menu

**Tools:**
- figlet, lolcat - Visual effects
- fx, jq - JSON processing
- btop - System monitoring

---

## 🎊 You Now Have:

✅ 11 working tools
✅ 3 AI models
✅ Interactive WebUI
✅ CLI tools (codex, playground)
✅ Beautiful visualizations
✅ Complete API system
✅ Auto-reload development server
✅ JSON processing tools
✅ System monitoring
✅ Rainbow ASCII art! 🌈

**HAVE FUN!** 🎮🚀✨
