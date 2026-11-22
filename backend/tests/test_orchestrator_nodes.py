"""
Unit tests for LangGraph workflow nodes and state transitions.
Tests actual graph node functions and full orchestrator end-to-end runs via ainvoke.
STRICT RULE: No source file is modified.
"""
import pytest
from app.agents.multi_agent_orchestrator import (
    create_multi_agent_orchestrator,
    run_domain_agents_node,
    run_hybrid_risk_engine_node,
    generate_recommendations_node,
    gather_adapter_data_node,
)


REPO = "owner/my-repo"
RELEASE = "v2.0.0"


def _git_data_wrapped():
    """run_domain_agents_node reads state['git_data']['metrics'] key."""
    return {
        "metrics": {
            "code_churn": 800, "files_changed": 20, "lines_added": 500,
            "lines_deleted": 300, "unique_contributors": 3, "pr_count": 4,
            "avg_pr_merge_time_hours": 24.0, "high_risk_files_touched": 1, "commit_count": 10
        }
    }


def _test_data():
    return {
        "total_tests": 1000, "passed_tests": 1000, "failed_tests": 0, "skipped_tests": 0,
        "pass_rate_pct": 100.0, "coverage_pct": 86.0, "coverage_delta_pct": 0.0,
        "flaky_tests_count": 0, "duration_seconds": 300.0, "untested_critical_modules": []
    }


def _defect_data():
    return {
        "open_blockers": 0, "open_critical": 0, "open_major": 0,
        "defect_density_per_kloc": 0.3, "bug_escape_rate_pct": 0.0,
        "regression_defects": 0, "mttr_hours": 0.0, "blocker_tickets": []
    }


def _ops_data():
    return {
        "pipeline_success_rate_pct": 100.0, "recent_failed_pipelines": 0,
        "staging_deploy_status": "HEALTHY", "staging_rollbacks_7d": 0,
        "infra_config_drift": False, "p95_latency_delta_ms": 0.0,
        "error_budget_burn_pct": 0.0
    }


def _base_request():
    return {
        "repository": REPO,
        "release": RELEASE,
        "scenario": "standard_healthy",
        "release_type": "MINOR",
        "target_environment": "production",
        "historical_window": 10,
        "custom_test_metrics": None,
        "custom_defect_metrics": None,
        "custom_operations_metrics": None,
    }


def _base_state():
    return {
        "request": _base_request(),
        "git_data": _git_data_wrapped(),
        "test_data": _test_data(),
        "defect_data": _defect_data(),
        "ops_data": _ops_data(),
    }


class TestOrchestratorNodes:

    @pytest.mark.asyncio
    async def test_run_domain_agents_produces_all_results(self):
        state = _base_state()
        result = await run_domain_agents_node(state)
        assert "code_result" in result
        assert "test_result" in result
        assert "defect_result" in result
        assert "ops_result" in result

    @pytest.mark.asyncio
    async def test_run_domain_agents_code_result_has_risk_score(self):
        state = _base_state()
        result = await run_domain_agents_node(state)
        assert "risk_score" in result["code_result"]

    @pytest.mark.asyncio
    async def test_run_domain_agents_ops_result_has_findings(self):
        state = _base_state()
        result = await run_domain_agents_node(state)
        assert "findings" in result["ops_result"]

    @pytest.mark.asyncio
    async def test_run_hybrid_risk_engine_node_has_risk_score(self):
        state = _base_state()
        agent_state = {**state, **(await run_domain_agents_node(state))}
        result = await run_hybrid_risk_engine_node(agent_state)
        assert "risk_score" in result
        assert 0.0 < result["risk_score"] < 1.0

    @pytest.mark.asyncio
    async def test_run_hybrid_risk_engine_node_has_risk_level(self):
        state = _base_state()
        agent_state = {**state, **(await run_domain_agents_node(state))}
        result = await run_hybrid_risk_engine_node(agent_state)
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    @pytest.mark.asyncio
    async def test_run_hybrid_risk_engine_node_has_breakdown(self):
        state = _base_state()
        agent_state = {**state, **(await run_domain_agents_node(state))}
        result = await run_hybrid_risk_engine_node(agent_state)
        assert "hybrid_engine" in result
        assert "hard_gate_triggered" in result["hybrid_engine"]

    @pytest.mark.asyncio
    async def test_generate_recommendations_node_has_actions(self):
        state = _base_state()
        agent_state = {**state, **(await run_domain_agents_node(state))}
        engine_state = {**agent_state, **(await run_hybrid_risk_engine_node(agent_state))}
        result = await generate_recommendations_node(engine_state)
        assert "recommendations" in result
        assert "required_actions" in result
        assert len(result["required_actions"]) >= 1

    @pytest.mark.asyncio
    async def test_gather_adapter_data_node_returns_all_sources(self):
        """Adapter gather node returns all 4 data sources."""
        state = {"request": _base_request()}
        result = await gather_adapter_data_node(state)
        assert "git_data" in result
        assert "test_data" in result
        assert "defect_data" in result
        assert "ops_data" in result

    @pytest.mark.asyncio
    async def test_full_graph_analyze_healthy(self):
        """End-to-end LangGraph orchestrator run for standard_healthy scenario."""
        graph = create_multi_agent_orchestrator()
        final_state = await graph.ainvoke({"request": _base_request()})
        report = final_state["final_report"]
        assert report["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert 0.0 < report["risk_score"] < 1.0

    @pytest.mark.asyncio
    async def test_full_graph_analyze_blocker(self):
        """End-to-end graph run for blocker_defects → hard gate triggered."""
        graph = create_multi_agent_orchestrator()
        req = {**_base_request(), "scenario": "blocker_defects"}
        final_state = await graph.ainvoke({"request": req})
        report = final_state["final_report"]
        assert report["risk_level"] in ("CRITICAL", "HIGH")
        assert report["hybrid_engine"]["hard_gate_triggered"] is True

    @pytest.mark.asyncio
    async def test_full_graph_has_required_actions(self):
        graph = create_multi_agent_orchestrator()
        final_state = await graph.ainvoke({"request": _base_request()})
        report = final_state["final_report"]
        assert isinstance(report["required_actions"], list)
        assert len(report["required_actions"]) >= 1

    @pytest.mark.asyncio
    async def test_full_graph_has_all_agents(self):
        graph = create_multi_agent_orchestrator()
        final_state = await graph.ainvoke({"request": _base_request()})
        report = final_state["final_report"]
        assert "code_agent" in report
        assert "test_agent" in report
        assert "defect_agent" in report
        assert "operations_agent" in report

    @pytest.mark.asyncio
    async def test_full_graph_ops_instability_high_or_critical(self):
        graph = create_multi_agent_orchestrator()
        req = {**_base_request(), "scenario": "ops_instability"}
        final_state = await graph.ainvoke({"request": req})
        report = final_state["final_report"]
        assert report["risk_level"] in ("CRITICAL", "HIGH")
