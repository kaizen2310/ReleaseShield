from typing import Dict, Any
from app.adapters.base import BaseAdapter

class TestAdapter(BaseAdapter):
    """
    Test suite & Coverage adapter.
    Simulates CI test telemetry (JUnit, pytest, Jest, SonarQube)
    designed to interface with CI pipelines or mock test data.
    """
    async def fetch_data(self, repository: str, release: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if context.get("custom_test_metrics"):
            return context["custom_test_metrics"]
            
        scenario = context.get("scenario", "standard_healthy")
        
        if scenario == "test_regression":
            return {
                "total_tests": 1420,
                "passed_tests": 1295,
                "failed_tests": 85,
                "skipped_tests": 40,
                "pass_rate_pct": 91.2, # Significant failure rate
                "coverage_pct": 71.4,
                "coverage_delta_pct": -8.6, # Major coverage drop
                "flaky_tests_count": 12,
                "duration_seconds": 1240.0,
                "untested_critical_modules": ["auth_service.py", "payment_processor.py", "session_store.ts"]
            }
        elif scenario == "high_risk_hotfix":
            return {
                "total_tests": 680,
                "passed_tests": 650,
                "failed_tests": 12,
                "skipped_tests": 18,
                "pass_rate_pct": 95.6,
                "coverage_pct": 76.0,
                "coverage_delta_pct": -4.2,
                "flaky_tests_count": 4,
                "duration_seconds": 450.0,
                "untested_critical_modules": ["hotfix_patch_handler.py"]
            }
        elif scenario == "blocker_defects":
            return {
                "total_tests": 1560,
                "passed_tests": 1540,
                "failed_tests": 12,
                "skipped_tests": 8,
                "pass_rate_pct": 98.7,
                "coverage_pct": 82.5,
                "coverage_delta_pct": -1.1,
                "flaky_tests_count": 2,
                "duration_seconds": 880.0,
                "untested_critical_modules": []
            }
        else: # standard_healthy
            return {
                "total_tests": 1650,
                "passed_tests": 1648,
                "failed_tests": 0,
                "skipped_tests": 2,
                "pass_rate_pct": 100.0,
                "coverage_pct": 86.4,
                "coverage_delta_pct": +1.2, # Improved coverage
                "flaky_tests_count": 0,
                "duration_seconds": 720.0,
                "untested_critical_modules": []
            }
