"""
Unit tests for HybridRiskEngine.
Tests deterministic blending, hard gates, trend calculation.
STRICT RULE: No source file is modified.
"""
import pytest
from app.services.hybrid_risk_engine import HybridRiskEngine
from app.schemas.unified_risk import AgentResult, Severity, RiskTrend


def _make_agent(name: str, score: float, level: Severity, metrics: dict) -> AgentResult:
    return AgentResult(
        agent_name=name,
        risk_score=score,
        risk_level=level,
        confidence=0.90,
        summary=f"{name} summary",
        metrics=metrics,
        findings=[]
    )


def _healthy_agents():
    code = _make_agent("Code / Git Agent", 0.10, Severity.LOW, {
        "code_churn": 800, "files_changed": 20, "avg_pr_merge_time_hours": 24.0,
        "high_risk_files_touched": 1
    })
    test = _make_agent("Test Agent", 0.05, Severity.LOW, {
        "pass_rate_pct": 100.0, "coverage_delta_pct": 0.0, "flaky_tests_count": 0
    })
    defect = _make_agent("Defect Agent", 0.05, Severity.LOW, {
        "open_blockers": 0, "open_critical": 0, "defect_density_per_kloc": 0.3,
        "staging_rollbacks_7d": 0
    })
    ops = _make_agent("Operations Agent", 0.05, Severity.LOW, {
        "pipeline_success_rate_pct": 100.0, "staging_rollbacks_7d": 0, "infra_config_drift": False
    })
    return code, test, defect, ops


class TestHybridRiskEngine:

    def test_healthy_scenario_low_risk(self):
        code, test, defect, ops = _healthy_agents()
        score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert score < 0.40
        assert level == Severity.LOW
        assert breakdown.hard_gate_triggered is False

    def test_hard_gate_a_open_blockers(self):
        """Gate A: open_blockers > 0 → score >= 0.90, CRITICAL"""
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 2
        score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert breakdown.hard_gate_triggered is True
        assert score >= 0.90
        assert level == Severity.CRITICAL

    def test_hard_gate_b_pass_rate(self):
        """Gate B: pass_rate_pct < 92 → score >= 0.80"""
        code, test, defect, ops = _healthy_agents()
        test.metrics["pass_rate_pct"] = 90.0
        score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert breakdown.hard_gate_triggered is True
        assert score >= 0.80

    def test_hard_gate_c_staging_rollbacks(self):
        """Gate C: staging_rollbacks >= 2 → score >= 0.85"""
        code, test, defect, ops = _healthy_agents()
        ops.metrics["staging_rollbacks_7d"] = 2
        score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert breakdown.hard_gate_triggered is True
        assert score >= 0.85

    def test_gate_a_takes_priority_over_gate_b(self):
        """Gate A fires first (elif chain) when both blockers and pass_rate fail."""
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 1
        test.metrics["pass_rate_pct"] = 85.0
        score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(code, test, defect, ops)
        # Gate A should fire (blocker)
        assert "BLOCKER" in breakdown.hard_gate_reason

    def test_trend_stable_no_history(self):
        code, test, defect, ops = _healthy_agents()
        _, _, _, _, trend = HybridRiskEngine.evaluate(code, test, defect, ops, previous_scores=[])
        assert trend == RiskTrend.STABLE

    def test_trend_stable_small_delta(self):
        code, test, defect, ops = _healthy_agents()
        _, _, _, _, trend = HybridRiskEngine.evaluate(code, test, defect, ops, previous_scores=[0.15])
        # Both scores are low, delta < 0.08
        assert trend == RiskTrend.STABLE

    def test_trend_increasing(self):
        """Prev score 0.10, final score must exceed prev+0.08 to be INCREASING."""
        code, test, defect, ops = _healthy_agents()
        # Drive score up with critical defects
        defect.metrics["open_blockers"] = 2  # hard gate fires, score = 0.90
        defect.risk_score = 0.95
        score, _, _, _, trend = HybridRiskEngine.evaluate(
            code, test, defect, ops, previous_scores=[0.10]
        )
        assert trend == RiskTrend.INCREASING

    def test_trend_decreasing(self):
        """Prev score 0.90, final healthy score 0.10 → DECREASING."""
        code, test, defect, ops = _healthy_agents()
        _, _, _, _, trend = HybridRiskEngine.evaluate(
            code, test, defect, ops, previous_scores=[0.90]
        )
        assert trend == RiskTrend.DECREASING

    def test_breakdown_scores_populated(self):
        code, test, defect, ops = _healthy_agents()
        _, _, breakdown, _, _ = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert 0.0 <= breakdown.xgboost_risk_score <= 1.0
        assert 0.0 <= breakdown.deterministic_rule_score <= 1.0
        assert 0.0 <= breakdown.blended_risk_score <= 1.0

    def test_risk_drivers_list(self):
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 1
        _, _, _, drivers, _ = HybridRiskEngine.evaluate(code, test, defect, ops)
        # Drivers returned (may be 0 for all-healthy scenario but should be a list)
        assert isinstance(drivers, list)

    def test_deterministic_score_weighted_sum(self):
        """Verify deterministic score = weighted sum of agent scores."""
        c_score, t_score, d_score, o_score = 0.60, 0.40, 0.70, 0.50
        expected_det = (0.60 * 0.25 + 0.40 * 0.25 + 0.70 * 0.30 + 0.50 * 0.20)
        code = _make_agent("Code", c_score, Severity.HIGH, {
            "code_churn": 0, "files_changed": 0, "avg_pr_merge_time_hours": 24.0, "high_risk_files_touched": 0
        })
        test = _make_agent("Test", t_score, Severity.MEDIUM, {
            "pass_rate_pct": 100.0, "coverage_delta_pct": 0.0, "flaky_tests_count": 0
        })
        defect = _make_agent("Defect", d_score, Severity.HIGH, {
            "open_blockers": 0, "open_critical": 0, "defect_density_per_kloc": 0.0
        })
        ops = _make_agent("Ops", o_score, Severity.MEDIUM, {
            "pipeline_success_rate_pct": 100.0, "staging_rollbacks_7d": 0, "infra_config_drift": False
        })
        _, _, breakdown, _, _ = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert abs(breakdown.deterministic_rule_score - round(min(max(expected_det, 0.05), 1.0), 2)) < 0.01

    def test_final_score_clamped_between_0_02_and_0_99(self):
        code, test, defect, ops = _healthy_agents()
        score, _, _, _, _ = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert 0.02 <= score <= 0.99

    def test_severity_thresholds(self):
        """Score >=0.80 → CRITICAL, >=0.60 → HIGH, >=0.30 → MEDIUM, else LOW."""
        code, test, defect, ops = _healthy_agents()
        defect.metrics["open_blockers"] = 3  # will force >= 0.90
        defect.risk_score = 0.95
        score, level, _, _, _ = HybridRiskEngine.evaluate(code, test, defect, ops)
        assert score >= 0.80
        assert level == Severity.CRITICAL
