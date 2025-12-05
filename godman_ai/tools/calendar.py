"""Calendar Tool - Manage calendar events."""

from typing import Any, Dict, List
import os
from datetime import datetime, timedelta


class CalendarTool:
    """Interact with Google Calendar."""
    
    name = "calendar"
    description = "Manage calendar events"
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Perform calendar operations.
        
        Args:
            action: 'list', 'create', 'update', 'delete'
            **kwargs: Action-specific parameters
            
        Returns:
            Dict with operation results
        """
        if action == "list":
            return self.list_events(**kwargs)
        elif action == "create":
            return self.create_event(**kwargs)
        elif action == "update":
            return self.update_event(**kwargs)
        elif action == "delete":
            return self.delete_event(**kwargs)
        else:
            return {"error": f"Unknown action: {action}"}
    
    def list_events(self, days_ahead: int = 7, **kwargs) -> Dict[str, Any]:
        """List upcoming calendar events."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
        except ImportError:
            return {"error": "google-api-python-client not installed. Run: pip install google-api-python-client google-auth"}
        
        creds_path = os.path.expanduser("~/.godman/google_calendar_token.json")
        if not os.path.exists(creds_path):
            return {"error": "Calendar credentials not found. Run authentication setup first."}
        
        try:
            creds = Credentials.from_authorized_user_file(creds_path)
            service = build('calendar', 'v3', credentials=creds)
            
            now = datetime.utcnow().isoformat() + 'Z'
            end = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=end,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    "id": event['id'],
                    "summary": event.get('summary', 'No title'),
                    "start": start,
                    "end": event['end'].get('dateTime', event['end'].get('date')),
                    "location": event.get('location', '')
                })
            
            return {
                "success": True,
                "count": len(formatted_events),
                "events": formatted_events
            }
        except Exception as e:
            return {"error": f"Failed to list events: {str(e)}"}
    
    def create_event(self, summary: str, start_time: str, end_time: str, description: str = "", location: str = "", **kwargs) -> Dict[str, Any]:
        """Create a new calendar event."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
        except ImportError:
            return {"error": "google-api-python-client not installed"}
        
        creds_path = os.path.expanduser("~/.godman/google_calendar_token.json")
        if not os.path.exists(creds_path):
            return {"error": "Calendar credentials not found"}
        
        try:
            creds = Credentials.from_authorized_user_file(creds_path)
            service = build('calendar', 'v3', credentials=creds)
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {'dateTime': start_time, 'timeZone': 'America/New_York'},
                'end': {'dateTime': end_time, 'timeZone': 'America/New_York'},
            }
            
            created_event = service.events().insert(calendarId='primary', body=event).execute()
            
            return {
                "success": True,
                "event_id": created_event['id'],
                "summary": summary,
                "link": created_event.get('htmlLink')
            }
        except Exception as e:
            return {"error": f"Failed to create event: {str(e)}"}
    
    def update_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        """Update an existing calendar event."""
        return {"error": "Not implemented yet"}
    
    def delete_event(self, event_id: str, **kwargs) -> Dict[str, Any]:
        """Delete a calendar event."""
        return {"error": "Not implemented yet"}
