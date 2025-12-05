#!/usr/bin/env python3
"""
GitHub Code Search Tool
Search for code across GitHub repositories using the GitHub API.
"""
import os
import sys
import argparse
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("Error: 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

load_dotenv()

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)


def search_code(query: str, language: Optional[str] = None, 
                max_results: int = 10, sort: str = "best-match") -> List[Dict]:
    """
    Search for code on GitHub.
    
    Args:
        query: Search query string
        language: Filter by programming language (optional)
        max_results: Maximum number of results to return
        sort: Sort order (best-match, indexed)
    
    Returns:
        List of search results
    """
    # Build search query
    search_query = query
    if language:
        search_query += f" language:{language}"
    
    # Prepare API request
    url = f"{GITHUB_API_BASE}/search/code"
    params = {
        "q": search_query,
        "sort": sort,
        "per_page": min(max_results, 100)  # GitHub API max per page is 100
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data.get("items", [])
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            # Check if it's rate limiting or permission issue
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            if rate_limit_remaining == '0':
                print(f"Error: API rate limit exceeded.")
            else:
                print(f"Error: Authentication required or insufficient permissions.")
            print(f"Set GITHUB_TOKEN in .env for higher rate limits.")
        else:
            print(f"HTTP Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return []


def search_repositories(query: str, language: Optional[str] = None,
                       max_results: int = 10, sort: str = "stars") -> List[Dict]:
    """
    Search for repositories on GitHub.
    
    Args:
        query: Search query string
        language: Filter by programming language (optional)
        max_results: Maximum number of results to return
        sort: Sort order (stars, forks, updated, help-wanted-issues)
    
    Returns:
        List of repository results
    """
    # Build search query
    search_query = query
    if language:
        search_query += f" language:{language}"
    
    # Prepare API request
    url = f"{GITHUB_API_BASE}/search/repositories"
    params = {
        "q": search_query,
        "sort": sort,
        "per_page": min(max_results, 100)
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        return data.get("items", [])
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            # Check if it's rate limiting or permission issue
            rate_limit_remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            if rate_limit_remaining == '0':
                print(f"Error: API rate limit exceeded.")
            else:
                print(f"Error: Authentication required or insufficient permissions.")
            print(f"Set GITHUB_TOKEN in .env for higher rate limits.")
        else:
            print(f"HTTP Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return []


def format_code_result(item: Dict) -> str:
    """Format a code search result for display."""
    repo_name = item.get("repository", {}).get("full_name", "Unknown")
    file_path = item.get("path", "Unknown")
    url = item.get("html_url", "")
    
    return f"""
Repository: {repo_name}
File: {file_path}
URL: {url}
"""


def format_repo_result(item: Dict) -> str:
    """Format a repository search result for display."""
    name = item.get("full_name", "Unknown")
    description = item.get("description", "No description")
    stars = item.get("stargazers_count", 0)
    language = item.get("language", "Unknown")
    url = item.get("html_url", "")
    
    return f"""
Repository: {name}
Description: {description}
Language: {language} | Stars: {stars}
URL: {url}
"""


def main():
    parser = argparse.ArgumentParser(
        description="Search for code on GitHub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for code
  python github_search.py --code "function calculate_total" --language python
  
  # Search for repositories
  python github_search.py --repos "machine learning" --language python --max 5
  
  # Search with authentication (set GITHUB_TOKEN in .env)
  python github_search.py --code "process receipts OCR"
        """
    )
    
    parser.add_argument("--code", help="Search for code snippets")
    parser.add_argument("--repos", help="Search for repositories")
    parser.add_argument("--language", help="Filter by programming language")
    parser.add_argument("--max", type=int, default=10, help="Maximum results (default: 10)")
    parser.add_argument("--sort", help="Sort order (for repos: stars, forks, updated)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.code and not args.repos:
        parser.error("Either --code or --repos must be specified")
    
    if args.code and args.repos:
        parser.error("Cannot specify both --code and --repos")
    
    # Perform search
    if args.code:
        print(f"Searching for code: {args.code}")
        if args.language:
            print(f"Language filter: {args.language}")
        print("-" * 80)
        
        results = search_code(
            query=args.code,
            language=args.language,
            max_results=args.max,
            sort=args.sort or "best-match"
        )
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("No results found.")
            else:
                print(f"Found {len(results)} results:\n")
                for i, item in enumerate(results, 1):
                    print(f"Result {i}:")
                    print(format_code_result(item))
    
    elif args.repos:
        print(f"Searching for repositories: {args.repos}")
        if args.language:
            print(f"Language filter: {args.language}")
        print("-" * 80)
        
        results = search_repositories(
            query=args.repos,
            language=args.language,
            max_results=args.max,
            sort=args.sort or "stars"
        )
        
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            if not results:
                print("No results found.")
            else:
                print(f"Found {len(results)} results:\n")
                for i, item in enumerate(results, 1):
                    print(f"Result {i}:")
                    print(format_repo_result(item))


if __name__ == "__main__":
    main()
