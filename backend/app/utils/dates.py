from datetime import datetime

def parse_github_date(date_str: str) -> datetime:
    """Parses standard GitHub ISO-8601 date strings."""
    if not date_str:
        return None
    
    # GitHub uses formats like "2024-05-14T18:00:00Z"
    date_str = date_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        # Fallback if the format is slightly different
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
