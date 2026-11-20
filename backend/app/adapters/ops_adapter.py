from typing import Dict, Any
from app.adapters.base import BaseAdapter

class OperationsAdapter(BaseAdapter):
    """
    Operations & Deployment Telemetry Adapter.
    Interfaces with CI/CD pipeline results (GitHub Actions, GitLab CI, ArgoCD)
    and APM / staging environment observability (Datadog, Prometheus).
    """
    async def fetch_data(self, repository: str, release: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if context.get("custom_operations_metrics"):
            return context["custom_operations_metrics"]
            
        scenario = context.get("scenario", "standard_healthy")
        
        if scenario == "ops_instability":
            return {
                "pipeline_success_rate_pct": 68.5, # High pipeline failure rate
                "recent_failed_pipelines": 6,
                "staging_deploy_status": "DEGRADED",
                "staging_rollbacks_7d": 2, # Staging rollbacks detected
                "infra_config_drift": True, # Kubernetes/Helm/Terraform drift
                "p95_latency_delta_ms": 145.0, # Degraded response time
                "error_budget_burn_pct": 32.0 # Critical error budget burn
            }
        elif scenario == "high_risk_hotfix":
            return {
                "pipeline_success_rate_pct": 82.0,
                "recent_failed_pipelines": 2,
                "staging_deploy_status": "HEALTHY",
                "staging_rollbacks_7d": 1,
                "infra_config_drift": False,
                "p95_latency_delta_ms": 35.0,
                "error_budget_burn_pct": 12.0
            }
        elif scenario == "test_regression":
            return {
                "pipeline_success_rate_pct": 88.0,
                "recent_failed_pipelines": 3,
                "staging_deploy_status": "HEALTHY",
                "staging_rollbacks_7d": 0,
                "infra_config_drift": False,
                "p95_latency_delta_ms": 15.0,
                "error_budget_burn_pct": 5.0
            }
        else: # standard_healthy
            return {
                "pipeline_success_rate_pct": 99.2,
                "recent_failed_pipelines": 0,
                "staging_deploy_status": "HEALTHY",
                "staging_rollbacks_7d": 0,
                "infra_config_drift": False,
                "p95_latency_delta_ms": -4.0, # Improved latency
                "error_budget_burn_pct": 0.8
            }
