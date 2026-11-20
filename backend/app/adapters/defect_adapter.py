from typing import Dict, Any
from app.adapters.base import BaseAdapter

class DefectAdapter(BaseAdapter):
    """
    Defect tracking adapter (Jira, GitHub Issues, Bugzilla).
    Provides structured metrics on open blocker/critical defects, defect density,
    bug escape rate, and MTTR.
    """
    async def fetch_data(self, repository: str, release: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if context.get("custom_defect_metrics"):
            return context["custom_defect_metrics"]
            
        scenario = context.get("scenario", "standard_healthy")
        
        if scenario == "blocker_defects":
            return {
                "open_blockers": 2,
                "open_critical": 4,
                "open_major": 7,
                "defect_density_per_kloc": 2.85, # Very high defect density
                "bug_escape_rate_pct": 14.5,
                "regression_defects": 3,
                "mttr_hours": 36.5,
                "blocker_tickets": ["RS-102 (P0: Auth Token Invalidation Failure)", "RS-109 (P0: Payment Checkout NullPointer)"]
            }
        elif scenario == "high_risk_hotfix":
            return {
                "open_blockers": 1,
                "open_critical": 2,
                "open_major": 4,
                "defect_density_per_kloc": 1.75,
                "bug_escape_rate_pct": 8.0,
                "regression_defects": 1,
                "mttr_hours": 14.0,
                "blocker_tickets": ["RS-204 (P0: Memory leak in cache worker under peak load)"]
            }
        elif scenario == "test_regression":
            return {
                "open_blockers": 0,
                "open_critical": 3,
                "open_major": 5,
                "defect_density_per_kloc": 1.2,
                "bug_escape_rate_pct": 6.5,
                "regression_defects": 2,
                "mttr_hours": 22.0,
                "blocker_tickets": []
            }
        else: # standard_healthy
            return {
                "open_blockers": 0,
                "open_critical": 0,
                "open_major": 1,
                "defect_density_per_kloc": 0.25,
                "bug_escape_rate_pct": 1.5,
                "regression_defects": 0,
                "mttr_hours": 8.0,
                "blocker_tickets": []
            }
