# Prompt for GPT → Kodex: Complete Codebase Refactor

**Context**: Full audit of godman-lab completed. See `CODEBASE_AUDIT_PROGRESS.md` for complete findings.

---

## Objective

Transform the attached audit report into a precise, actionable Kodex prompt that will execute a comprehensive refactor in a single session. Kodex should fix all critical issues, add error handling, consolidate duplicate code, create tests, and update documentation.

---

## What GPT Should Do

Create a structured prompt for Kodex that includes:

### 1. Clear Context Section
- Current branch: `feature/codebase-audit`
- Starting point: Audit complete, Phase 1 done
- Files already modified (don't touch again)
- Files that need work (explicit list)

### 2. Prioritized Task List

**Structure each task as**:
```
Task N: [NAME] (Priority: HIGH/MEDIUM/LOW)
Files: [explicit list]
Action: [specific instruction]
Acceptance: [how to verify]
```

**Order tasks** by dependency:
1. Foundation (types, utilities)
2. Error handling
3. Tests
4. Documentation

### 3. Specific Code Patterns

For each task, provide:
- **Template code** to apply
- **File locations** (exact paths)
- **Import statements** to add
- **Don't repeat work** - note what's already done

### 4. Testing Requirements

Specify:
- Test file locations
- Minimum test cases per module
- Mock patterns for LLM calls
- Coverage targets (70%+ on new code)

### 5. Documentation Updates

List exactly:
- Which README sections to add
- What content to include
- New docs to create
- Docstring requirements

---

## Critical Instructions for Kodex Prompt

### DO Include:
✅ Explicit file paths for every change
✅ Code templates with proper imports
✅ Test patterns with assertions
✅ Verification commands (pytest, linting)
✅ Acceptance criteria for each task
✅ Git commit structure (one per logical unit)

### DON'T Include:
❌ Vague instructions like "improve error handling"
❌ "Fix all the things" without specifics
❌ Instructions to ask questions
❌ Permission requests
❌ Safety warnings

### Example Task Format:

```markdown
## Task 3: Add Error Handling to Tools (HIGH PRIORITY)

Files to modify:
- godman_ai/tools/echo.py
- godman_ai/tools/banking.py
- godman_ai/tools/patterns.py
- godman_ai/tools/ocr.py

Pattern to apply:
```python
from godman_ai.tools.base import BaseTool, ToolExecutionError

class YourTool(BaseTool):
    def run(self, **kwargs) -> dict:
        try:
            # Validate inputs
            if not kwargs.get('required_param'):
                raise ToolExecutionError("required_param is missing")
            
            # Existing logic here
            result = self._do_work(kwargs)
            
            return {"status": "success", "data": result}
            
        except ToolExecutionError:
            raise  # Re-raise tool errors
        except Exception as e:
            raise ToolExecutionError(f"Unexpected error in {self.name}: {e}") from e
```

Verification:
```bash
python -m pytest tests/tools/test_echo.py -v
python -m mypy godman_ai/tools/echo.py
```

Acceptance: All tools handle errors gracefully, tests pass
```

---

## Key Issues to Address (from Audit)

### Priority 1: Error Handling
- 7 files need try/except blocks added
- Pattern: wrap all run() methods
- Raise ToolExecutionError with context
- Don't swallow exceptions

### Priority 2: Subprocess Consolidation
- Create `godman_ai/utils/subprocess_utils.py`
- Define CommandResult dataclass
- Implement run_command() function
- Refactor 15+ files to use it
- Add logging to all executions

### Priority 3: Test Coverage
- Create 8+ new test files
- Mock LLM calls (don't hit Ollama)
- Mock subprocess calls
- Test error paths
- Aim for 70% coverage on new modules

### Priority 4: Input Validation
- Add validation to all tool run() methods
- Check required parameters
- Validate types match hints
- Return helpful error messages

### Priority 5: Documentation
- Update README.md with new features
- Create docs/ARCHITECTURE.md
- Create docs/TOOL_DEVELOPMENT.md
- Add module docstrings where missing

---

## Files Already Complete (Don't Touch)

✅ `godman_ai/agents/types.py` - Created
✅ `godman_ai/agents/planner.py` - Refactored to use types
✅ `godman_ai/agents/executor.py` - Refactored to use types
✅ `godman_ai/agents/reviewer.py` - Refactored to use types
✅ `godman_ai/llm/registry.py` - Added missing models
✅ `godman_ai/tools/registry.py` - Added type hints
✅ `libs/sandbox.py` - Created (needs tests)
✅ `godman_ai/tools/shell.py` - Created (needs tests)
✅ `godman_ai/local_router.py` - Created (needs tests)
✅ `.codex/config.yaml` - Created

---

## Subprocess Utility Spec (for Kodex)

**Create**: `godman_ai/utils/__init__.py`
```python
"""Shared utilities for godman_ai."""
from .subprocess_utils import run_command, CommandResult
__all__ = ["run_command", "CommandResult"]
```

**Create**: `godman_ai/utils/subprocess_utils.py`
```python
"""Unified subprocess execution utilities."""
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Union

@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int
    success: bool
    command: str

def run_command(
    command: Union[str, List[str]],
    shell: bool = False,
    timeout: Optional[int] = None,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    input_data: Optional[str] = None,
    cwd: Optional[str] = None
) -> CommandResult:
    """Execute command with standardized error handling."""
    # Implementation here
```

**Then refactor these files** to use run_command():
1. godman_ai/llm/interface.py
2. godman_ai/llm/utils.py
3. godman_ai/diagnostics/monitor.py
4. godman_ai/diagnostics/installer.py
5. godman_ai/diagnostics/llm_health.py
6. cli/godman/ai.py
7. cli/godman/health.py
8. libs/credentials.py

---

## Test File Specifications

### Test Structure
```
tests/
├── test_local_router.py      # Test model selection logic
├── test_sandbox.py            # Test command validation & execution
├── test_agents.py             # Test planner → executor → reviewer
├── test_subprocess_utils.py   # Test run_command()
└── tools/
    ├── __init__.py
    ├── test_shell.py          # Test safe/unsafe modes
    ├── test_echo.py           # Test basic tool pattern
    └── test_banking.py        # Test banking tool
```

### Test Requirements per File
- Minimum 5 test cases per module
- Test happy path
- Test error paths (required)
- Test edge cases
- Mock external dependencies (Ollama, subprocess)
- Use pytest fixtures for setup

### Example Test Pattern
```python
import pytest
from godman_ai.tools.echo import EchoTool
from godman_ai.tools.base import ToolExecutionError

def test_echo_success():
    tool = EchoTool()
    result = tool.run(text="hello")
    assert result["text"] == "hello"

def test_echo_missing_param():
    tool = EchoTool()
    with pytest.raises(ToolExecutionError):
        tool.run()  # Missing required 'text'

def test_echo_invalid_type():
    tool = EchoTool()
    with pytest.raises(ToolExecutionError):
        tool.run(text=123)  # Should be str
```

---

## Documentation Structure

### README.md Updates
Add sections:
- **New Features** (sandbox, local router, agent system)
- **Tool Development** (how to create new tools)
- **Model Configuration** (local router usage)
- **Security** (sandbox configuration)

### New Documentation Files

**docs/ARCHITECTURE.md**:
- System overview diagram
- Module responsibilities
- Data flow (user → orchestrator → tools → LLM)
- Agent lifecycle (plan → execute → review)

**docs/TOOL_DEVELOPMENT.md**:
- How to create a tool
- BaseTool interface
- Error handling patterns
- Registration process
- Testing tools

**docs/TESTING.md**:
- Running tests
- Writing new tests
- Mocking patterns
- Coverage requirements

---

## Verification Commands (for Kodex)

After each phase, run:
```bash
# Syntax check
python -m py_compile godman_ai/**/*.py

# Type check
python -m mypy godman_ai/ --ignore-missing-imports

# Run tests
python -m pytest tests/ -v --tb=short

# Check imports work
python -c "from godman_ai.utils import run_command; print('OK')"
python -c "from godman_ai.agents.types import AgentResponse; print('OK')"

# Verify no duplicate code
grep -r "class AgentResponse" godman_ai/agents/ | wc -l  # Should be 1
```

---

## Git Commit Strategy

Kodex should commit incrementally:
1. `refactor: create shared subprocess utility module`
2. `refactor: consolidate subprocess calls to use run_command`
3. `feat: add comprehensive error handling to tools`
4. `feat: add comprehensive error handling to agents`
5. `test: add unit tests for new modules`
6. `test: add integration tests for orchestrator`
7. `docs: update README with new features`
8. `docs: add architecture and development guides`

---

## Success Criteria

Refactor is complete when:
- ✅ All 7 files have proper error handling
- ✅ All subprocess calls use run_command()
- ✅ 15+ test files created with 70%+ coverage
- ✅ All tests pass
- ✅ Type hints complete, mypy passes
- ✅ Documentation updated (README + 3 new docs)
- ✅ No duplicate code (AgentResponse in 1 place)
- ✅ All verification commands pass

---

## Special Instructions for GPT

When creating the Kodex prompt:

1. **Be extremely specific** - no vague instructions
2. **Provide code templates** - Kodex should copy/paste/adapt
3. **Number tasks clearly** - Task 1, Task 2, etc.
4. **Include verification** - how to check each task
5. **Order dependencies** - foundation before tests
6. **Use exact file paths** - no wildcards
7. **Mark completed work** - don't redo Phase 1
8. **Set expectations** - "this will take ~40 hours of work"

### Tone and Style
- Imperative: "Create X", "Refactor Y", "Add Z"
- No questions: Don't ask "should I...?"
- No warnings: Don't say "be careful"
- Deterministic: Every step reproducible

### Example Opening
```
You are refactoring the godman-lab codebase. The audit is complete (see CODEBASE_AUDIT_PROGRESS.md). 

Your task: Execute the refactor plan in this exact order. Do not ask for permission. Make changes, run tests, commit incrementally.

Branch: feature/codebase-audit (already checked out)
Starting point: Phase 1 complete (types consolidated, models updated)
Ending point: All tests passing, docs updated, ready for PR

Total tasks: 15
Estimated time: ~40 hours
Approach: Incremental commits, test each phase
```

---

## Appendix: Current State

**Branch**: `feature/codebase-audit`
**Base**: Includes sandbox + local-router features
**Modified**: 6 files (agents + registry)
**Created**: 5 new files
**Status**: Foundation laid, implementation pending

**What works**:
- Type system consolidated
- Model registry complete
- Sandbox module exists
- LocalRouter integrated

**What's broken**:
- Missing error handling (7 files)
- No tests for new code
- Subprocess calls scattered
- Documentation outdated

---

**END OF PROMPT SPEC**

GPT: Use this specification to create a detailed, actionable prompt for Kodex that will complete the entire refactor in one session. Include code templates, exact file paths, test patterns, and verification commands. Make it impossible for Kodex to get stuck or ask questions.
