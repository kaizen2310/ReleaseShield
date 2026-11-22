"""
Unit tests for RecommendationEngine.
Tests action generation for all trigger conditions.
STRICT RULE: No source file is modified.
"""
import pytest
from app.services.recommendation_engine import RecommendationEngine
from app.schemas.unified_risk import AgentResult, Severity, ActionPriority


def _make_agent(name: str, score: float, level: Severity, metrics: dict) -> AgentResult:
    return AgentResult(
        agent_name=name,
        risk_score=score,
        risk_level=level,
        confidence=0.90,
        summary="summary",
        metrics=metrics,
        findings=[]
    )


def _healthy_agents():
    code = _make_agent("Code", 0.10, Severity.LOW, {
        "code_churn": 800, "files_changed": 20, "avg_pr_merge_time_hours": 24.0,
        "high_risk_files_touched": 1, "pr_count": 5
    })
    test = _make_agent("Test", 0.05, Severity.LOW, {
        "pass_rate_pct": 100.0, "failed_tests": 0, "coverage_pct": 86.0,
        "coverage_delta_pct": 0.0, "flaky_tests_count": 0
    })
    defect = _make_agent("Defect", 0.05, Severity.LOW, {
        "open_blockers": 0, "open_critical": 0, "blocker_tickets": [],
        "defect_density_per_kloc": 0.3, "regression_defects": 0
    })
    ops = _make_agent("Ops", 0.05, Severity.LOW, {
        "staging_rollbacks_7d": 0, "infra_config_drift": False,
        "pipeline_success_rate_pct": 100.0, "error_budget_burn_pct": 0.0
    })
    return code, test, defect, ops


class TestRecommendationEngine:

    def test_healthy_has_mandatory_approval_action(self):
        code, test, defect, ops = _healthy_agents()
        recs, actions = RecommendationEngine.generate(code, test, defect, ops, "LOW")
        gov_actions = [a for a in actions if a.category == "GOVERNANCE"]
        assert len(gov_actions) >= 1

    def test_healthy_has_one_recommendation(self):
        code, test, defect, ops = _healthy_agents()
        recs, _ = RecommendationEngine.generate(code, test, defect, ops, "LOW")
        assert len(recs) >= 1
        assert "nominal" in recs[0].lower() or "canary" in recs[0].lower()

    def test_blocker_generates_blocker_action(self):
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 2
        defect.metrics["blocker_tickets"] = ["RS-102", "RS-109"]
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "CRITICAL")
        blocker_actions = [a for a in actions if a.priority == ActionPriority.BLOCKER and a.category == "DEFECT"]
        assert len(blocker_actions) >= 1
        assert actions[0].id.startswith("ACT-DEF")

    def test_blocker_id_format(self):
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 1
        defect.metrics["blocker_tickets"] = ["JIRA-1"]
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "CRITICAL")
        defect_actions = [a for a in actions if a.category == "DEFECT"]
        assert defect_actions[0].id.startswith("ACT-DEF-01")

    def test_open_critical_3_generates_triage_action(self):
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_critical"] = 3
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        triage = [a for a in actions if "Triage" in a.title]
        assert len(triage) >= 1

    def test_pass_rate_below_95_generates_test_action(self):
        code, test, defect, ops = _healthy_agents()
        test.metrics["pass_rate_pct"] = 92.0
        test.metrics["failed_tests"] = 80
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        test_actions = [a for a in actions if a.category == "TEST" and "Fix" in a.title]
        assert len(test_actions) >= 1

    def test_pass_rate_below_90_blocker_priority(self):
        code, test, defect, ops = _healthy_agents()
        test.metrics["pass_rate_pct"] = 88.0
        test.metrics["failed_tests"] = 120
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "CRITICAL")
        test_blocker = [a for a in actions if a.category == "TEST" and a.priority == ActionPriority.BLOCKER]
        assert len(test_blocker) >= 1

    def test_pass_rate_between_90_95_high_priority(self):
        code, test, defect, ops = _healthy_agents()
        test.metrics["pass_rate_pct"] = 92.0
        test.metrics["failed_tests"] = 80
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        test_high = [a for a in actions if a.category == "TEST" and a.priority == ActionPriority.HIGH]
        assert len(test_high) >= 1

    def test_coverage_delta_below_minus_3_generates_action(self):
        code, test, defect, ops = _healthy_agents()
        test.metrics["coverage_delta_pct"] = -4.0
        test.metrics["coverage_pct"] = 80.0
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "MEDIUM")
        cov_actions = [a for a in actions if "Coverage" in a.title]
        assert len(cov_actions) >= 1

    def test_flaky_tests_generates_isolate_action(self):
        code, test, defect, ops = _healthy_agents()
        test.metrics["flaky_tests_count"] = 3
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "MEDIUM")
        flaky_actions = [a for a in actions if "Flaky" in a.title]
        assert len(flaky_actions) >= 1
        assert flaky_actions[0].priority == ActionPriority.MEDIUM

    def test_staging_rollbacks_generates_runbook_action(self):
        code, test, defect, ops = _healthy_agents()
        ops.metrics["staging_rollbacks_7d"] = 1
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        rb_actions = [a for a in actions if "Rollback" in a.title or "Migration" in a.title]
        assert len(rb_actions) >= 1

    def test_infra_config_drift_generates_action(self):
        code, test, defect, ops = _healthy_agents()
        ops.metrics["infra_config_drift"] = True
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        drift_actions = [a for a in actions if "Config" in a.title or "Drift" in a.title]
        assert len(drift_actions) >= 1

    def test_pipeline_below_90_generates_stability_action(self):
        code, test, defect, ops = _healthy_agents()
        ops.metrics["pipeline_success_rate_pct"] = 85.0
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        pipe_actions = [a for a in actions if "Pipeline" in a.title or "CI/CD" in a.title]
        assert len(pipe_actions) >= 1

    def test_high_risk_files_5_generates_code_review_action(self):
        code, test, defect, ops = _healthy_agents()
        code.metrics["high_risk_files_touched"] = 5
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        code_actions = [a for a in actions if a.category == "CODE"]
        assert len(code_actions) >= 1

    def test_churn_above_6000_generates_code_review_action(self):
        code, test, defect, ops = _healthy_agents()
        code.metrics["code_churn"] = 7000
        code.metrics["high_risk_files_touched"] = 1
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "HIGH")
        code_actions = [a for a in actions if a.category == "CODE"]
        assert len(code_actions) >= 1

    def test_fast_pr_merge_generates_audit_action(self):
        code, test, defect, ops = _healthy_agents()
        code.metrics["avg_pr_merge_time_hours"] = 2.0
        code.metrics["pr_count"] = 5
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "MEDIUM")
        pr_actions = [a for a in actions if "PR" in a.title or "Fast-Tracked" in a.title or "Audit" in a.title]
        assert len(pr_actions) >= 1

    def test_risk_level_critical_mandatory_approval_blocker(self):
        code, test, defect, ops = _healthy_agents()
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "CRITICAL")
        gov = [a for a in actions if a.category == "GOVERNANCE"]
        assert gov[-1].priority == ActionPriority.BLOCKER

    def test_risk_level_low_mandatory_approval_high(self):
        code, test, defect, ops = _healthy_agents()
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "LOW")
        gov = [a for a in actions if a.category == "GOVERNANCE"]
        assert gov[-1].priority == ActionPriority.HIGH

    def test_action_ids_unique(self):
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 1
        defect.metrics["open_critical"] = 3
        ops.metrics["staging_rollbacks_7d"] = 1
        _, actions = RecommendationEngine.generate(code, test, defect, ops, "CRITICAL")
        ids = [a.id for a in actions]
        assert len(ids) == len(set(ids))
