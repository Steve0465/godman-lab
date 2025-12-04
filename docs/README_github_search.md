# GitHub Code Search Tool

A command-line utility to search for code and repositories on GitHub using the GitHub API.

## Features

- Search for code snippets across all public GitHub repositories
- Search for repositories by name, description, or topics
- Filter results by programming language
- Sort results by various criteria (stars, forks, updates, etc.)
- Output results in human-readable format or JSON

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Optional: Set up GitHub authentication** (recommended for higher rate limits)
   
   Without authentication, GitHub API limits you to 10 requests per minute. With authentication, you get 30 requests per minute.
   
   - Create a personal access token on GitHub:
     1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
     2. Click "Generate new token (classic)"
     3. Give it a name like "godman-lab-search"
     4. No special scopes needed for public searches
     5. Copy the token
   
   - Add to your `.env` file:
     ```
     GITHUB_TOKEN=your_github_token_here
     ```

## Usage

### Search for Code

Search for code snippets across GitHub repositories:

```bash
# Basic code search
python github_search.py --code "function calculate_total"

# Search with language filter
python github_search.py --code "OCR receipt processing" --language python

# Limit number of results
python github_search.py --code "pandas dataframe" --language python --max 5

# Output as JSON
python github_search.py --code "machine learning" --json
```

### Search for Repositories

Search for repositories by name, description, or topics:

```bash
# Search for repositories
python github_search.py --repos "receipt scanner"

# Search with language filter and sort by stars
python github_search.py --repos "automation scripts" --language python --sort stars

# Search and limit results
python github_search.py --repos "OCR" --language python --max 3
```

## Command-Line Options

- `--code QUERY` - Search for code snippets
- `--repos QUERY` - Search for repositories
- `--language LANG` - Filter by programming language (e.g., python, javascript, go)
- `--max N` - Maximum number of results to return (default: 10)
- `--sort ORDER` - Sort order:
  - For code: `best-match` (default), `indexed`
  - For repos: `stars` (default), `forks`, `updated`, `help-wanted-issues`
- `--json` - Output results as JSON instead of human-readable format

## Examples

### Find Python receipt processing code
```bash
python github_search.py --code "receipt OCR tesseract" --language python --max 5
```

### Find popular machine learning repositories
```bash
python github_search.py --repos "machine learning" --language python --sort stars --max 10
```

### Search for expense tracking tools
```bash
python github_search.py --repos "expense tracker" --max 5
```

### Get JSON output for further processing
```bash
python github_search.py --code "streamlit dashboard" --json > results.json
```

## Rate Limits

- **Unauthenticated**: 10 requests per minute
- **Authenticated**: 30 requests per minute

If you hit rate limits, the tool will notify you. Add a `GITHUB_TOKEN` to your `.env` file to increase limits.

## Tips

1. Use specific search terms for better results
2. Combine language filters with your queries for more relevant results
3. Use quotes in your query for exact phrase matching: `--code "def process_receipt"`
4. GitHub's search supports many operators like `in:file`, `repo:owner/name`, `stars:>1000`
5. For repository searches, sort by stars to find the most popular projects

## Integration with Your Workflow

You can use this tool to:
- Find similar projects before starting new code
- Discover libraries and tools for specific tasks
- Learn from existing implementations
- Find code examples for specific functions or patterns
- Identify popular repositories in your area of interest

## Troubleshooting

**Error: 'requests' library is required**
- Run: `pip install requests`

**Error: API rate limit exceeded**
- Add a `GITHUB_TOKEN` to your `.env` file
- Wait a minute before making more requests

**No results found**
- Try broader search terms
- Remove or change the language filter
- Check your internet connection
