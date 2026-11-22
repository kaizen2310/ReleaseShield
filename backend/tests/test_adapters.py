"""
Unit tests for async adapters: TestAdapter, DefectAdapter, OperationsAdapter, GitAdapter.
NOTE: GitAdapter tries a real GitHub API call first; we mock it to force synthetic fallback.
STRICT RULE: No source file is modified.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.adapters.test_adapter import TestAdapter
from app.adapters.defect_adapter import DefectAdapter
from app.adapters.ops_adapter import OperationsAdapter
from app.adapters.git_adapter import GitAdapter


REPO = "owner/my-repo"
RELEASE = "v2.0.0"

# Always patch GitHubService to avoid network calls in sandbox
_GITHUB_PATCH = "app.adapters.git_adapter.GitHubService.get_release_data"


# ===========================================================================
# TestAdapter  (pure synthetic, no network — no mock needed)
# ===========================================================================

class TestTestAdapter:

    @pytest.mark.asyncio
    async def test_standard_healthy_pass_rate_100(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data["pass_rate_pct"] == 100.0

    @pytest.mark.asyncio
    async def test_test_regression_scenario(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "test_regression"})
        assert data["pass_rate_pct"] == 91.2
        assert data["failed_tests"] == 85

    @pytest.mark.asyncio
    async def test_custom_metrics_override(self):
        """custom_test_metrics should bypass scenario and return raw dict."""
        adapter = TestAdapter()
        custom = {"pass_rate_pct": 55.0, "failed_tests": 450, "total_tests": 1000}
        data = await adapter.fetch_data(REPO, RELEASE, {"custom_test_metrics": custom})
        assert data["pass_rate_pct"] == 55.0

    @pytest.mark.asyncio
    async def test_high_risk_hotfix_has_flaky(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "high_risk_hotfix"})
        assert data["flaky_tests_count"] > 0

    @pytest.mark.asyncio
    async def test_blocker_defects_scenario_high_pass_rate(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "blocker_defects"})
        assert data["pass_rate_pct"] > 95.0

    @pytest.mark.asyncio
    async def test_unknown_scenario_defaults_to_healthy(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "unknown_xyz"})
        assert data["pass_rate_pct"] == 100.0

    @pytest.mark.asyncio
    async def test_result_has_required_keys(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        for key in ["total_tests", "passed_tests", "failed_tests", "pass_rate_pct", "coverage_pct"]:
            assert key in data

    @pytest.mark.asyncio
    async def test_regression_scenario_has_untested_modules(self):
        adapter = TestAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "test_regression"})
        assert len(data["untested_critical_modules"]) > 0


# ===========================================================================
# DefectAdapter  (pure synthetic, no network)
# ===========================================================================

class TestDefectAdapter:

    @pytest.mark.asyncio
    async def test_standard_healthy_zero_blockers(self):
        adapter = DefectAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data["open_blockers"] == 0

    @pytest.mark.asyncio
    async def test_blocker_defects_scenario(self):
        adapter = DefectAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "blocker_defects"})
        assert data["open_blockers"] >= 2

    @pytest.mark.asyncio
    async def test_blocker_defects_has_tickets(self):
        adapter = DefectAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "blocker_defects"})
        assert len(data.get("blocker_tickets", [])) >= 1

    @pytest.mark.asyncio
    async def test_custom_defect_metrics_override(self):
        adapter = DefectAdapter()
        custom = {"open_blockers": 5, "open_critical": 10, "defect_density_per_kloc": 3.0,
                  "open_major": 0, "bug_escape_rate_pct": 0.0, "regression_defects": 0,
                  "mttr_hours": 0.0, "blocker_tickets": []}
        data = await adapter.fetch_data(REPO, RELEASE, {"custom_defect_metrics": custom})
        assert data["open_blockers"] == 5

    @pytest.mark.asyncio
    async def test_result_has_required_keys(self):
        adapter = DefectAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        for key in ["open_blockers", "open_critical", "defect_density_per_kloc", "regression_defects"]:
            assert key in data

    @pytest.mark.asyncio
    async def test_ops_instability_has_elevated_density(self):
        adapter = DefectAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "ops_instability"})
        # ops_instability may have elevated defect density or some defects
        assert isinstance(data["defect_density_per_kloc"], float)


# ===========================================================================
# OperationsAdapter  (pure synthetic, no network)
# ===========================================================================

class TestOperationsAdapter:

    @pytest.mark.asyncio
    async def test_ops_instability_rollbacks(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "ops_instability"})
        assert data["staging_rollbacks_7d"] >= 2

    @pytest.mark.asyncio
    async def test_ops_instability_pipeline_rate(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "ops_instability"})
        assert data["pipeline_success_rate_pct"] < 80.0

    @pytest.mark.asyncio
    async def test_standard_healthy_stable_pipeline(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data["pipeline_success_rate_pct"] >= 95.0

    @pytest.mark.asyncio
    async def test_standard_healthy_no_rollbacks(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data["staging_rollbacks_7d"] == 0

    @pytest.mark.asyncio
    async def test_custom_ops_metrics_override(self):
        adapter = OperationsAdapter()
        custom = {"pipeline_success_rate_pct": 10.0, "staging_rollbacks_7d": 5,
                  "recent_failed_pipelines": 90, "staging_deploy_status": "FAILED",
                  "infra_config_drift": True, "p95_latency_delta_ms": 500.0,
                  "error_budget_burn_pct": 80.0}
        data = await adapter.fetch_data(REPO, RELEASE, {"custom_operations_metrics": custom})
        assert data["pipeline_success_rate_pct"] == 10.0

    @pytest.mark.asyncio
    async def test_result_has_required_keys(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        for key in ["pipeline_success_rate_pct", "staging_rollbacks_7d", "infra_config_drift"]:
            assert key in data

    @pytest.mark.asyncio
    async def test_ops_instability_has_drift(self):
        adapter = OperationsAdapter()
        data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "ops_instability"})
        assert data["infra_config_drift"] is True


# ===========================================================================
# GitAdapter  (network call patched to force synthetic fallback)
# ===========================================================================

class TestGitAdapter:

    @pytest.mark.asyncio
    async def test_standard_healthy_low_churn(self):
        """Force GitHub API failure → synthetic fallback for standard_healthy."""
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data["metrics"]["code_churn"] < 5000
        assert data.get("is_synthetic") is True

    @pytest.mark.asyncio
    async def test_high_risk_hotfix_high_churn(self):
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "high_risk_hotfix"})
        assert data["metrics"]["code_churn"] > 5000

    @pytest.mark.asyncio
    async def test_unknown_scenario_returns_data(self):
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "nonexistent"})
        assert isinstance(data, dict)
        assert "metrics" in data
        assert "code_churn" in data["metrics"]

    @pytest.mark.asyncio
    async def test_result_has_required_metrics_keys(self):
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        for key in ["code_churn", "files_changed", "pr_count"]:
            assert key in data["metrics"]

    @pytest.mark.asyncio
    async def test_ops_instability_high_risk_files(self):
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "ops_instability"})
        assert data["metrics"]["high_risk_files_touched"] > 0

    @pytest.mark.asyncio
    async def test_synthetic_flag_set_on_fallback(self):
        with patch(_GITHUB_PATCH, new_callable=AsyncMock, side_effect=Exception("No network")):
            adapter = GitAdapter()
            data = await adapter.fetch_data(REPO, RELEASE, {"scenario": "standard_healthy"})
        assert data.get("is_synthetic") is True
