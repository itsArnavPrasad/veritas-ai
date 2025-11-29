# date_time_tool.py
"""Tool to fetch current date and time for temporal context in fact-checking."""
from datetime import datetime
from google.adk.tools import FunctionTool
from typing import Dict


def get_current_datetime() -> Dict[str, str]:
    """
    Fetches the current date and time in UTC.
    
    Returns:
        Dictionary containing:
        - current_datetime_iso: ISO-8601 formatted datetime string (e.g., "2025-01-15T10:30:00Z")
        - current_date: Date string (e.g., "2025-01-15")
        - current_time: Time string (e.g., "10:30:00")
        - timezone: Timezone information (e.g., "UTC")
    """
    now = datetime.utcnow()
    return {
        "current_datetime_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "timezone": "UTC",
        "timestamp": str(int(now.timestamp())),
    }


# Create the function tool for ADK
current_datetime_tool = FunctionTool(
    func=get_current_datetime,
)

