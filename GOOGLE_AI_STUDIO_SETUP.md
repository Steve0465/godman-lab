# Google AI Studio Integration Guide

Step-by-step guide to integrate the Trello enhancement with Google AI Studio (formerly Gemini Studio).

## What is Google AI Studio?

Google AI Studio is a web-based IDE for prototyping with Gemini models. You can:
- Set system instructions for the AI
- Test prompts and responses
- Generate code with context
- Export to code (Python, JavaScript, etc.)

## Step 1: Access Google AI Studio

1. Go to: **https://aistudio.google.com/**
2. Sign in with your Google account
3. Click **"Create new"** → **"New prompt"**

## Step 2: Add System Instructions

The system instructions tell the AI how to behave and what conventions to follow.

### Option A: Use Pre-Made Instructions (Recommended)

Copy the entire content from:
```
GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md
```

**How to paste:**
1. In AI Studio, look for **"System instructions"** section (usually at the top)
2. Click the text area or **"Add system instruction"** button
3. Paste the entire content from `GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md`
4. Click **"Save"** or **"Apply"**

### Option B: Customize Instructions

If you want to customize, edit `GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md` first, then paste.

Key sections in the instructions:
- React + TypeScript principles
- File naming conventions
- JSDoc requirements
- Gemini Vision API patterns
- Trello API patterns
- UI/UX guidelines for pool professionals
- Testing requirements

## Step 3: Provide Context (Optional but Recommended)

To help the AI understand your codebase, you can provide context about the existing modules.

### Upload Key Files as Context

In AI Studio, you can upload files or provide code snippets:

**Files to upload (select relevant ones):**
```
godman_ai/tools/trello.py
godman_ai/workflows/part_identifier_workflow.py
libs/trello_client.py
tests/tools/test_trello.py
PART_IDENTIFIER_TRELLO_README.md
```

**How to upload:**
1. Look for **"Add file"** or **"Upload"** button
2. Select files from your local system
3. AI Studio will index them for context

### Provide Code Snippets in Prompt

Alternatively, include relevant code in your first prompt:

```
I'm working on a pool part identifier app. Here's the existing workflow:

[paste godman_ai/workflows/part_identifier_workflow.py]

Please help me integrate Google Gemini Vision API into the _analyze_part_step method.
```

## Step 4: Start Building with AI

Now you can prompt the AI to generate code that follows your conventions.

### Example Prompts

**1. Integrate Gemini Vision API**
```
Replace the _analyze_part_step placeholder with actual Gemini Vision API integration.
Requirements:
- Use google-generativeai library
- Accept image file as input
- Extract part number, manufacturer, confidence
- Handle API errors with retry logic
- Return structured result matching existing format
```

**2. Create React Component**
```
Create a PartCard.tsx component that displays part identification results.
Requirements:
- Show part number, confidence, description
- Include favorite star toggle button
- Display alternatives as expandable section
- Follow the UI guidelines (large touch targets, high contrast)
```

**3. Add Cross-Reference Database**
```
Replace the _enrich_equivalents_step with a function that looks up cross-references
from a SQLite database. Include:
- Database schema for parts and equivalents
- Query to find matching parts
- Error handling
```

## Step 5: Model Configuration

Configure the Gemini model for optimal code generation:

### Recommended Settings

**Model:** `gemini-1.5-pro-latest` or `gemini-1.5-flash-latest`
- Pro: Better for complex code generation, slower
- Flash: Faster responses, good for most tasks

**Temperature:** `0.2` to `0.4`
- Lower = more deterministic, consistent
- Higher = more creative, varied

**Max Output Tokens:** `8192`
- Allows for larger code blocks

**Safety Settings:** Default (adjust if needed)

### How to Configure

1. Look for **"Model"** dropdown at top
2. Select `gemini-1.5-pro-latest`
3. Click **"Run settings"** or gear icon ⚙️
4. Adjust Temperature, Max tokens
5. Save settings

## Step 6: Generate Code

### Best Practices for Prompts

**Be Specific:**
```
❌ "Add Gemini API"
✅ "Integrate Gemini Vision API in _analyze_part_step to analyze pool part images"
```

**Provide Context:**
```
✅ "Using the existing PartIdentifierWorkflow class, add a method to save 
   identification results to SQLite. The database should have tables for 
   parts, identifications, and user feedback."
```

**Reference Conventions:**
```
✅ "Create a FavoriteButton.tsx component following the Artesian Pools conventions:
   - Use TypeScript with strict typing
   - Name file in kebab-case
   - Add JSDoc comments
   - Use useState for favorite state
   - Follow mobile-first design"
```

**Request Tests:**
```
✅ "Also generate Jest tests for this component using React Testing Library.
   Mock the favorites manager."
```

## Step 7: Iterate and Refine

AI Studio allows you to chat with the AI to refine the code:

**Follow-up prompts:**
```
"Add error handling for network failures"
"Make this function async"
"Add TypeScript types for the return value"
"Update the test to cover edge cases"
```

**Review and Adjust:**
1. Review generated code
2. Ask for corrections if needed
3. Test locally
4. Iterate until satisfied

## Step 8: Export Code

Once you have working code:

1. Click **"Get code"** or **"Export"** button
2. Select language (Python, JavaScript, etc.)
3. Copy code to your project
4. Run tests to verify

## Example Workflow: Gemini Vision Integration

### Step-by-Step

**1. Set System Instructions**
- Paste `GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md` into system instructions

**2. Upload Context**
- Upload `godman_ai/workflows/part_identifier_workflow.py`
- Upload `libs/trello_client.py` (for reference)

**3. First Prompt**
```
I need to integrate Google Gemini Vision API into the PartIdentifierWorkflow.

Current code in _analyze_part_step:
[paste the placeholder code]

Requirements:
- Install google-generativeai package
- Use environment variable GEMINI_API_KEY
- Send image file to Gemini Vision
- Prompt: "Identify this pool part. Provide: part number, manufacturer, 
  confidence score (0-1), description, dimensions if visible"
- Parse JSON response
- Handle errors (rate limits, invalid images, API failures)
- Return format matching current mock data structure

Follow all conventions from system instructions.
```

**4. Review Generated Code**
- AI will provide implementation
- Review for correctness
- Ask follow-ups if needed

**5. Request Tests**
```
Now generate pytest tests for this implementation. Mock the Gemini API calls.
Include tests for:
- Successful identification
- API errors
- Rate limiting with retry
- Invalid image format
```

**6. Copy to Project**
```bash
# Copy generated code to your project
code godman_ai/workflows/part_identifier_workflow.py
# Paste the AI-generated code, replacing placeholder

# Copy tests
code tests/workflows/test_gemini_vision.py
# Paste generated tests

# Run tests
pytest tests/workflows/test_gemini_vision.py -v
```

## Tips for Best Results

### ✅ Do's

- **Be explicit** about conventions (the system instructions help)
- **Provide examples** of existing code style
- **Request tests** alongside implementation
- **Iterate** - ask for refinements
- **Review carefully** - AI can make mistakes
- **Test thoroughly** - always run tests locally

### ❌ Don'ts

- **Don't assume** AI knows your codebase structure
- **Don't skip** system instructions setup
- **Don't trust blindly** - always review generated code
- **Don't forget** to handle edge cases
- **Don't commit** without testing

## Common Issues and Solutions

### Issue: AI generates code that doesn't follow conventions

**Solution:**
- Ensure system instructions are properly set
- Reference specific conventions in prompt:
  ```
  "Follow the kebab-case naming convention from system instructions"
  ```

### Issue: AI uses wrong imports

**Solution:**
- Provide import examples in prompt:
  ```
  "Import from godman_ai.workflows like this:
  from godman_ai.workflows import PartIdentifierWorkflow"
  ```

### Issue: Generated code has syntax errors

**Solution:**
- Ask AI to fix: "There's a syntax error on line 42, please fix it"
- Provide error message: "Getting error: SyntaxError: invalid syntax"

### Issue: AI doesn't match existing architecture

**Solution:**
- Upload relevant existing files as context
- Show examples:
  ```
  "Match this pattern from existing code:
  [paste example]"
  ```

## Advanced: Multi-File Projects

For larger features spanning multiple files:

### Approach 1: Sequential Generation

1. Generate main module first
2. Then tests
3. Then documentation
4. Then example usage

### Approach 2: Use Conversation History

Keep the conversation going to maintain context:

```
Prompt 1: "Create FavoritesButton.tsx component..."
Prompt 2: "Now create a custom hook useFavorites to manage favorite state..."
Prompt 3: "Add tests for both the component and hook..."
Prompt 4: "Document the usage in markdown..."
```

### Approach 3: Project Templates

Create a prompt template for new features:

```
Feature: [FEATURE_NAME]
Location: [FILE_PATH]
Description: [DESCRIPTION]

Requirements:
- [REQUIREMENT_1]
- [REQUIREMENT_2]

Integration:
- Imports from: [MODULES]
- Exports: [EXPORTS]
- Tests location: [TEST_PATH]

Follow all system instructions for conventions.
```

## Resources

**Official Documentation:**
- Google AI Studio: https://aistudio.google.com/
- Gemini API Docs: https://ai.google.dev/docs
- Python SDK: https://github.com/google/generative-ai-python

**Your Documentation:**
- System Instructions: `GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md`
- Architecture Guide: `PART_IDENTIFIER_TRELLO_README.md`
- Quick Reference: `TRELLO_QUICK_START.md`

## Troubleshooting

### Can't find System Instructions field

**AI Studio Interface:**
1. Look for **"System instructions"** at the top of the page
2. Or click **"Configure"** → **"System instructions"**
3. On mobile: Expand the settings menu

### Code doesn't match conventions

**Check:**
1. System instructions are properly saved
2. Instructions are in the **System instructions** field (not regular chat)
3. Model is `gemini-1.5-pro` or newer

### Generated code has errors

**Steps:**
1. Copy error message
2. Paste in AI Studio: "Fix this error: [ERROR]"
3. Provide context: "This happens when I [ACTION]"
4. Review fix carefully

## Next Steps

Once comfortable with AI Studio:

1. **Integrate Gemini Vision** for real part recognition
2. **Build React components** for the UI
3. **Create database schema** for parts
4. **Add cross-reference lookup** functionality
5. **Implement Google Sheets logging**

**Ready to start?**
1. Open: https://aistudio.google.com/
2. Paste system instructions from `GEMINI_STUDIO_SYSTEM_INSTRUCTIONS.md`
3. Start prompting with your first feature!

---

**Happy coding with AI! 🚀**
