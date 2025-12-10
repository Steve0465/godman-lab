import logging
from typing import Dict, Any

from libs.att_scraper import ATTClient


logger = logging.getLogger(__name__)


def run_att_status(query: str) -> str:
    """
    Get AT&T account status information.
    
    Retrieves network status, outages, repair tickets, and service information
    from AT&T account. Can filter results based on user query.
    
    Args:
        query: User query specifying what information to retrieve
               (e.g., "tickets", "outages", "billing", "network status", "all")
    
    Returns:
        Filtered status information as formatted string
    """
    logger.info(f"Running ATT status tool with query: {query}")
    
    try:
        # Normalize query
        query_lower = query.lower()
        
        # Get full status data
        with ATTClient() as client:
            data = client.get_status()
        
        # Filter based on user intent
        if "ticket" in query_lower or "repair" in query_lower:
            return _format_tickets(data)
        elif "outage" in query_lower:
            return _format_outages(data)
        elif "network" in query_lower or "status" in query_lower:
            return _format_network_status(data)
        elif "region" in query_lower or "service" in query_lower or "location" in query_lower:
            return _format_service_region(data)
        elif "case" in query_lower or "number" in query_lower:
            return _format_case_numbers(data)
        else:
            # Return all information
            return _format_full_status(data)
    
    except Exception as e:
        logger.error(f"Error getting AT&T status: {e}")
        return f"Error retrieving AT&T status: {str(e)}"


def _format_tickets(data: Dict[str, Any]) -> str:
    """Format repair tickets information."""
    result = ["=== AT&T Repair Tickets ===\n"]
    
    if data.get("repair_tickets"):
        for i, ticket in enumerate(data["repair_tickets"], 1):
            result.append(f"{i}. {ticket}")
    else:
        result.append("No open repair tickets found.")
    
    if data.get("case_numbers"):
        result.append(f"\nCase Numbers: {', '.join(data['case_numbers'])}")
    
    result.append(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)


def _format_outages(data: Dict[str, Any]) -> str:
    """Format outage information."""
    result = ["=== AT&T Outages ===\n"]
    
    if data.get("outages"):
        for i, outage in enumerate(data["outages"], 1):
            result.append(f"{i}. {outage}")
    else:
        result.append("No active outages reported.")
    
    result.append(f"\nNetwork Status: {data.get('network_status', 'Unknown')}")
    result.append(f"Timestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)


def _format_network_status(data: Dict[str, Any]) -> str:
    """Format network status information."""
    result = ["=== AT&T Network Status ===\n"]
    result.append(f"Status: {data.get('network_status', 'Unknown')}")
    
    if data.get("outages"):
        result.append(f"\nActive Outages: {len(data['outages'])}")
    
    if data.get("service_region"):
        result.append(f"Service Region: {data.get('service_region')}")
    
    result.append(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)


def _format_service_region(data: Dict[str, Any]) -> str:
    """Format service region information."""
    result = ["=== AT&T Service Region ===\n"]
    
    if data.get("service_region"):
        result.append(data["service_region"])
    else:
        result.append("Service region information not available.")
    
    result.append(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)


def _format_case_numbers(data: Dict[str, Any]) -> str:
    """Format case numbers."""
    result = ["=== AT&T Case Numbers ===\n"]
    
    if data.get("case_numbers"):
        for i, case_num in enumerate(data["case_numbers"], 1):
            result.append(f"{i}. {case_num}")
    else:
        result.append("No case numbers found.")
    
    result.append(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)


def _format_full_status(data: Dict[str, Any]) -> str:
    """Format complete status information."""
    result = ["=== AT&T Account Status ===\n"]
    
    result.append(f"Network Status: {data.get('network_status', 'Unknown')}")
    
    if data.get("service_region"):
        result.append(f"Service Region: {data.get('service_region')}")
    
    if data.get("outages"):
        result.append(f"\nActive Outages ({len(data['outages'])}):")
        for i, outage in enumerate(data["outages"], 1):
            result.append(f"  {i}. {outage}")
    else:
        result.append("\nActive Outages: None")
    
    if data.get("repair_tickets"):
        result.append(f"\nRepair Tickets ({len(data['repair_tickets'])}):")
        for i, ticket in enumerate(data["repair_tickets"], 1):
            result.append(f"  {i}. {ticket}")
    else:
        result.append("\nRepair Tickets: None")
    
    if data.get("case_numbers"):
        result.append(f"\nCase Numbers: {', '.join(data['case_numbers'])}")
    
    result.append(f"\nTimestamp: {data.get('timestamp', 'N/A')}")
    return "\n".join(result)
