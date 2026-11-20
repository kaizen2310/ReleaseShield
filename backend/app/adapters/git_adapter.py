from typing import Dict, Any, List
from app.adapters.base import BaseAdapter
from app.services.github_service import GitHubService
from app.services.metrics_service import MetricsService

class GitAdapter(BaseAdapter):
    """
    Git & Code changes adapter.
    Pulls real GitHub commit, file churn, and PR metrics if token is available,
    otherwise provides robust synthetic fallback for offline/demo operation.
    """
    async def fetch_data(self, repository: str, release: str, context: Dict[str, Any]) -> Dict[str, Any]:
        owner, name = repository.split("/") if "/" in repository else ("unknown", repository)
        
        # Check if custom override provided in context
        scenario = context.get("scenario", "standard_healthy")
        
        try:
            raw_data = await GitHubService.get_release_data(owner, name, release)
            target_date = raw_data["target_release"].get("published_at") or raw_data["target_release"].get("created_at")
            previous_date = raw_data["previous_release"].get("published_at") or raw_data["previous_release"].get("created_at")
            
            pull_requests = []
            if target_date and previous_date:
                try:
                    from app.github.prs import get_prs_between_dates
                    pull_requests = await get_prs_between_dates(owner, name, previous_date, target_date)
                except Exception:
                    pull_requests = []
                    
            metrics = MetricsService.calculate_metrics(raw_data, pull_requests)
            metrics_dict = metrics.model_dump()
            
            # Enrich with high_risk_files count
            high_risk_files = 0
            for f in raw_data.get("comparison", {}).get("files", []):
                filename = f.get("filename", "").lower()
                if any(x in filename for x in ["auth", "security", "config", "docker", "migration", "payment", "core"]):
                    high_risk_files += 1
            metrics_dict["high_risk_files_touched"] = high_risk_files
            return {
                "raw_release": raw_data,
                "metrics": metrics_dict,
                "is_synthetic": False
            }
        except Exception as e:
            # Fallback to realistic synthetic git metrics aligned with the scenario
            return self._generate_synthetic_git(repository, release, scenario)

    def _generate_synthetic_git(self, repository: str, release: str, scenario: str) -> Dict[str, Any]:
        if scenario == "high_risk_hotfix":
            metrics = {
                "commit_count": 48,
                "files_changed": 142,
                "lines_added": 8200,
                "lines_deleted": 1900,
                "code_churn": 10100,
                "unique_contributors": 19,
                "pr_count": 12,
                "avg_pr_merge_time_hours": 2.4, # rushed PRs
                "high_risk_files_touched": 14
            }
        elif scenario == "ops_instability":
            metrics = {
                "commit_count": 22,
                "files_changed": 35,
                "lines_added": 1400,
                "lines_deleted": 600,
                "code_churn": 2000,
                "unique_contributors": 6,
                "pr_count": 8,
                "avg_pr_merge_time_hours": 18.0,
                "high_risk_files_touched": 9 # Docker, K8s, config changes
            }
        else: # standard_healthy or default
            metrics = {
                "commit_count": 18,
                "files_changed": 24,
                "lines_added": 850,
                "lines_deleted": 320,
                "code_churn": 1170,
                "unique_contributors": 5,
                "pr_count": 7,
                "avg_pr_merge_time_hours": 24.5,
                "high_risk_files_touched": 2
            }
        return {
            "metrics": metrics,
            "is_synthetic": True,
            "simulated_scenario": scenario
        }
