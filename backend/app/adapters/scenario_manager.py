from typing import Dict, Any, List

class ScenarioManager:
    """
    Manages pre-configured scenario presets for ReleaseShield.
    Enables academic evaluation, demonstrations, and robust local testing without external tool dependencies.
    """
    PRESETS = [
        {
            "id": "standard_healthy",
            "name": "Standard Healthy Release",
            "description": "Routine release with clean code churn, 100% test pass rate, 0 blocker bugs, and stable CI/CD pipelines.",
            "expected_risk": "LOW"
        },
        {
            "id": "high_risk_hotfix",
            "name": "High Churn Hotfix / Rush Release",
            "description": "Urgent release characterized by massive code churn, fast merged PRs, elevated defect density, and reduced review thoroughness.",
            "expected_risk": "HIGH"
        },
        {
            "id": "test_regression",
            "name": "Test & Coverage Regression",
            "description": "Release exhibiting 8.6% drop in code coverage, 85 failing unit tests, and 12 flaky tests in critical payment & auth paths.",
            "expected_risk": "HIGH"
        },
        {
            "id": "blocker_defects",
            "name": "Critical Blocker Defects (Hard Gate)",
            "description": "Release with 2 unresolved P0 BLOCKER defects (RS-102 Auth Invalidation, RS-109 Payment Timeout) triggering mandatory release blocks.",
            "expected_risk": "CRITICAL"
        },
        {
            "id": "ops_instability",
            "name": "Operational & CI/CD Pipeline Instability",
            "description": "Release exhibiting 2 staging rollbacks, 31.5% pipeline failure rate, infrastructure config drift, and high error budget burn.",
            "expected_risk": "CRITICAL"
        }
    ]

    @classmethod
    def get_all_scenarios(cls) -> List[Dict[str, Any]]:
        return cls.PRESETS

    @classmethod
    def get_scenario(cls, scenario_id: str) -> Dict[str, Any]:
        for s in cls.PRESETS:
            if s["id"] == scenario_id:
                return s
        return cls.PRESETS[0]
