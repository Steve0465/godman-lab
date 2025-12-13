"""
Trello REST API Client

A minimal, production-ready Trello API client using simple REST calls.
Authenticates using API key and token via query parameters.

Usage:
    from libs.trello import TrelloClient
    
    client = TrelloClient()
    boards = client.get_boards()
    cards = client.get_board_cards(board_id="abc123")
"""

import os
import requests
from typing import Dict, List, Optional, Any


class TrelloAPIError(Exception):
    """Raised when Trello API returns an error"""
    pass


class TrelloAuthError(Exception):
    """Raised when authentication credentials are missing or invalid"""
    pass


class TrelloClient:
    """
    Trello REST API client.
    
    Requires environment variables:
        TRELLO_API_KEY: Your Trello API key
        TRELLO_TOKEN: Your Trello authentication token
    
    Get credentials from: https://trello.com/power-ups/admin
    """
    
    BASE_URL = "https://api.trello.com/1"
    
    def __init__(self, api_key: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Trello client.
        
        Args:
            api_key: Trello API key (optional, reads from TRELLO_API_KEY env var)
            token: Trello authentication token (optional, reads from TRELLO_TOKEN env var)
        
        Raises:
            TrelloAuthError: If credentials are missing
        """
        self.api_key = api_key or os.getenv('TRELLO_API_KEY')
        self.token = token or os.getenv('TRELLO_TOKEN')
        
        if not self.api_key:
            raise TrelloAuthError(
                "TRELLO_API_KEY not found. Set environment variable or pass api_key parameter.\n"
                "Get your API key from: https://trello.com/power-ups/admin"
            )
        
        if not self.token:
            raise TrelloAuthError(
                "TRELLO_TOKEN not found. Set environment variable or pass token parameter.\n"
                "Get your token from: https://trello.com/power-ups/admin"
            )
        
        self.session = requests.Session()
    
    def _request(
        self, 
        method: str, 
        path: str, 
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Make HTTP request to Trello API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path (without base URL)
            params: Query parameters (key and token will be added automatically)
            **kwargs: Additional arguments to pass to requests
        
        Returns:
            JSON response from API
        
        Raises:
            TrelloAPIError: If API returns an error
        """
        # Ensure path starts with /
        if not path.startswith('/'):
            path = '/' + path
        
        url = f"{self.BASE_URL}{path}"
        
        # Add auth credentials to params
        if params is None:
            params = {}
        
        params['key'] = self.api_key
        params['token'] = self.token
        
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                **kwargs
            )
            
            # Check for HTTP errors
            if response.status_code >= 400:
                error_msg = f"Trello API error {response.status_code}: {response.text}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg = f"Trello API error: {error_data['error']}"
                    elif 'message' in error_data:
                        error_msg = f"Trello API error: {error_data['message']}"
                except:
                    pass
                
                raise TrelloAPIError(error_msg)
            
            # Return JSON response
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise TrelloAPIError(f"Network error communicating with Trello: {e}")
    
    def get_me(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            Dictionary containing user information
        """
        return self._request('GET', '/members/me')
    
    def get_boards(self, fields: str = "id,name,url") -> List[Dict[str, Any]]:
        """
        Get all boards for the authenticated user.
        
        Args:
            fields: Comma-separated list of fields to return
                   Default: "id,name,url"
                   Available: id, name, desc, url, closed, idOrganization, etc.
        
        Returns:
            List of board dictionaries
        """
        params = {'fields': fields}
        return self._request('GET', '/members/me/boards', params=params)
    
    def get_board(self, board_id: str, **params) -> Dict[str, Any]:
        """
        Get a specific board by ID.
        
        Args:
            board_id: The board ID
            **params: Additional query parameters (e.g., fields, actions, cards, lists)
        
        Returns:
            Board dictionary
        """
        return self._request('GET', f'/boards/{board_id}', params=params)
    
    def get_board_cards(
        self, 
        board_id: str,
        fields: Optional[str] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        Get all cards from a board.
        
        Args:
            board_id: The board ID
            fields: Comma-separated list of fields to return
            **params: Additional query parameters
                     Common options:
                     - attachments: "true" or "cover"
                     - checklists: "all"
                     - members: "true"
        
        Returns:
            List of card dictionaries
        """
        if fields:
            params['fields'] = fields
        
        return self._request('GET', f'/boards/{board_id}/cards', params=params)
    
    def get_board_lists(
        self,
        board_id: str,
        fields: Optional[str] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        Get all lists from a board.
        
        Args:
            board_id: The board ID
            fields: Comma-separated list of fields to return
            **params: Additional query parameters
        
        Returns:
            List of list dictionaries
        """
        if fields:
            params['fields'] = fields
        
        return self._request('GET', f'/boards/{board_id}/lists', params=params)
    
    def get_card(
        self,
        card_id: str,
        fields: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Get a specific card by ID.
        
        Args:
            card_id: The card ID
            fields: Comma-separated list of fields to return
            **params: Additional query parameters
                     Common options:
                     - attachments: "true" or "cover"
                     - checklists: "all"
                     - members: "true"
        
        Returns:
            Card dictionary
        """
        if fields:
            params['fields'] = fields
        
        return self._request('GET', f'/cards/{card_id}', params=params)
    
    def get_list(
        self,
        list_id: str,
        fields: Optional[str] = None,
        **params
    ) -> Dict[str, Any]:
        """
        Get a specific list by ID.
        
        Args:
            list_id: The list ID
            fields: Comma-separated list of fields to return
            **params: Additional query parameters
        
        Returns:
            List dictionary
        """
        if fields:
            params['fields'] = fields
        
        return self._request('GET', f'/lists/{list_id}', params=params)
    
    def get_list_cards(
        self,
        list_id: str,
        fields: Optional[str] = None,
        **params
    ) -> List[Dict[str, Any]]:
        """
        Get all cards from a list.
        
        Args:
            list_id: The list ID
            fields: Comma-separated list of fields to return
            **params: Additional query parameters
        
        Returns:
            List of card dictionaries
        """
        if fields:
            params['fields'] = fields
        
        return self._request('GET', f'/lists/{list_id}/cards', params=params)
    
    def search(
        self,
        query: str,
        modelTypes: str = "cards,boards",
        **params
    ) -> Dict[str, Any]:
        """
        Search Trello for cards, boards, etc.
        
        Args:
            query: Search query
            modelTypes: Comma-separated types to search (cards, boards, members, organizations)
            **params: Additional query parameters
        
        Returns:
            Dictionary with search results
        """
        params['query'] = query
        params['modelTypes'] = modelTypes
        
        return self._request('GET', '/search', params=params)
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
