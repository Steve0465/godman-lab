"""Web Search Tool - Search the internet using multiple providers."""

from typing import Any, Dict
import json


class WebSearchTool:
    """Search the web using DuckDuckGo, Google, or other providers."""
    
    name = "web_search"
    description = "Search the internet for information"
    
    def run(self, query: str, provider: str = "duckduckgo", max_results: int = 10, **kwargs) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            provider: Search provider (duckduckgo, google, brave)
            max_results: Maximum number of results
            
        Returns:
            Dict with search results
        """
        try:
            if provider == "duckduckgo":
                return self._search_duckduckgo(query, max_results)
            elif provider == "google":
                return self._search_google(query, max_results)
            else:
                return {"error": f"Unknown provider: {provider}"}
        except Exception as e:
            return {"error": str(e), "query": query}
    
    def _search_duckduckgo(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return {"error": "duckduckgo-search not installed. Run: pip install duckduckgo-search"}
        
        try:
            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "snippet": r.get("body")
                    })
            
            return {
                "provider": "duckduckgo",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": f"DuckDuckGo search failed: {str(e)}"}
    
    def _search_google(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Google Custom Search API."""
        import os
        try:
            import requests
        except ImportError:
            return {"error": "requests not installed"}
        
        api_key = os.getenv("GOOGLE_API_KEY")
        cx = os.getenv("GOOGLE_SEARCH_CX")
        
        if not api_key or not cx:
            return {"error": "GOOGLE_API_KEY and GOOGLE_SEARCH_CX environment variables required"}
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": cx, "q": query, "num": min(max_results, 10)}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "url": item.get("link"),
                    "snippet": item.get("snippet")
                })
            
            return {
                "provider": "google",
                "query": query,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"error": f"Google search failed: {str(e)}"}
