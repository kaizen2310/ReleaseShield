from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAdapter(ABC):
    """
    Abstract Base Adapter for ReleaseShield external tool integrations.
    Provides standard interface for fetching or simulating metrics for git, tests, defects, and ops.
    """
    @abstractmethod
    async def fetch_data(self, repository: str, release: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch real or mock data for the given repository and release context."""
        pass
