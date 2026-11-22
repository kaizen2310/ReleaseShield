"""
Unit tests for the four domain agents:
  CodeAgent, TestAgent, DefectAgent, OperationsAgent.
STRICT RULE: No source file is modified. Tests only.
"""
import pytest
from pydantic import ValidationError
from app.agents.code_agent import CodeAgent
from app.agents.test_agent import TestAgent
from app.agents.defect_agent import DefectAgent
from app.agents.operations_agent import OperationsAgent
from app.schemas.unified_risk import Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _healthy_code():
    return {"commit_count": 5, "files_changed": 20, "lines_added": 500, "lines_deleted": 300,
            "code_churn": 800, "unique_contributors": 3, "pr_count": 4,
            "avg_pr_merge_time_hours": 24.0, "high_risk_files_touched": 1}

def _healthy_test():
    return {"total_tests": 1000, "passed_tests": 1000, "failed_tests": 0, "skipped_tests": 0,
            "pass_rate_pct": 100.0, "coverage_pct": 86.0, "coverage_delta_pct": 0.0,
            "flaky_tests_count": 0, "duration_seconds": 300.0, "untested_critical_modules": []}

def _healthy_defect():
    return {"open_blockers": 0, "open_critical": 0, "open_major": 0,
            "defect_density_per_kloc": 0.3, "bug_escape_rate_pct": 0.0,
            "regression_defects": 0, "mttr_hours": 0.0, "blocker_tickets": []}

def _healthy_ops():
    return {"pipeline_success_rate_pct": 100.0, "recent_failed_pipelines": 0,
            "staging_deploy_status": "HEALTHY", "staging_rollbacks_7d": 0,
            "infra_config_drift": False, "p95_latency_delta_ms": 0.0,
            "error_budget_burn_pct": 0.0}


# ===========================================================================
# CodeAgent Tests
# ===========================================================================

class TestCodeAgent:

    def test_healthy_metrics_low_risk(self):
        result = CodeAgent.evaluate(_healthy_code())
        assert result.risk_level == Severity.LOW
        assert result.risk_score < 0.40
        assert len(result.findings) == 0

    def test_churn_exactly_5000_no_finding(self):
        m = _healthy_code()
        m["code_churn"] = 5000
        result = CodeAgent.evaluate(m)
        code_churn_findings = [f for f in result.findings if f.category == "CODE_CHURN"]
        assert len(code_churn_findings) == 0

    def test_churn_5001_medium_finding(self):
        m = _healthy_code()
        m["code_churn"] = 5001
        result = CodeAgent.evaluate(m)
        churn_findings = [f for f in result.findings if f.category == "CODE_CHURN"]
        assert len(churn_findings) == 1
        assert churn_findings[0].severity == Severity.MEDIUM

    def test_churn_8001_high_finding(self):
        m = _healthy_code()
        m["code_churn"] = 8001
        result = CodeAgent.evaluate(m)
        churn_findings = [f for f in result.findings if f.category == "CODE_CHURN"]
        assert len(churn_findings) == 1
        assert churn_findings[0].severity == Severity.HIGH

    def test_files_80_no_finding(self):
        m = _healthy_code()
        m["files_changed"] = 80
        result = CodeAgent.evaluate(m)
        scope_findings = [f for f in result.findings if f.category == "CHANGE_SCOPE"]
        assert len(scope_findings) == 0

    def test_files_81_medium_finding(self):
        m = _healthy_code()
        m["files_changed"] = 81
        result = CodeAgent.evaluate(m)
        scope_findings = [f for f in result.findings if f.category == "CHANGE_SCOPE"]
        assert len(scope_findings) == 1
        assert scope_findings[0].severity == Severity.MEDIUM

    def test_files_121_high_finding(self):
        m = _healthy_code()
        m["files_changed"] = 121
        result = CodeAgent.evaluate(m)
        scope_findings = [f for f in result.findings if f.category == "CHANGE_SCOPE"]
        assert scope_findings[0].severity == Severity.HIGH

    def test_rushed_pr_review_triggered(self):
        m = _healthy_code()
        m["pr_count"] = 5
        m["avg_pr_merge_time_hours"] = 2.0
        result = CodeAgent.evaluate(m)
        rushed = [f for f in result.findings if f.category == "RUSHED_PR_REVIEW"]
        assert len(rushed) == 1
        assert rushed[0].severity == Severity.HIGH

    def test_rushed_pr_zero_pr_count_no_finding(self):
        """Guard: pr_count=0 means no rushed PR finding even if merge time is low."""
        m = _healthy_code()
        m["pr_count"] = 0
        m["avg_pr_merge_time_hours"] = 1.0
        result = CodeAgent.evaluate(m)
        rushed = [f for f in result.findings if f.category == "RUSHED_PR_REVIEW"]
        assert len(rushed) == 0

    def test_high_risk_files_4_no_finding(self):
        m = _healthy_code()
        m["high_risk_files_touched"] = 4
        result = CodeAgent.evaluate(m)
        critical = [f for f in result.findings if f.category == "CRITICAL_COMPONENTS"]
        assert len(critical) == 0

    def test_high_risk_files_5_medium(self):
        m = _healthy_code()
        m["high_risk_files_touched"] = 5
        result = CodeAgent.evaluate(m)
        critical = [f for f in result.findings if f.category == "CRITICAL_COMPONENTS"]
        assert len(critical) == 1
        assert critical[0].severity == Severity.MEDIUM

    def test_high_risk_files_10_high(self):
        m = _healthy_code()
        m["high_risk_files_touched"] = 10
        result = CodeAgent.evaluate(m)
        critical = [f for f in result.findings if f.category == "CRITICAL_COMPONENTS"]
        assert critical[0].severity == Severity.HIGH

    def test_zero_values_low_risk(self):
        m = {"commit_count": 0, "files_changed": 0, "lines_added": 0, "lines_deleted": 0,
             "code_churn": 0, "unique_contributors": 0, "pr_count": 0,
             "avg_pr_merge_time_hours": 0.0, "high_risk_files_touched": 0}
        result = CodeAgent.evaluate(m)
        assert result.risk_level == Severity.LOW
        assert len(result.findings) == 0

    def test_multiple_findings_max_score_wins(self):
        """With churn=9000 (HIGH=0.80) and files=130 (HIGH=0.70), score should be max."""
        m = _healthy_code()
        m["code_churn"] = 9000
        m["files_changed"] = 130
        result = CodeAgent.evaluate(m)
        assert result.risk_score >= 0.70
        assert len(result.findings) >= 2

    def test_agent_name_and_confidence(self):
        result = CodeAgent.evaluate(_healthy_code())
        assert result.agent_name == "Code / Git Agent"
        assert result.confidence == 0.90

    def test_metrics_in_result(self):
        m = _healthy_code()
        result = CodeAgent.evaluate(m)
        assert "code_churn" in result.metrics
        assert result.metrics["code_churn"] == m["code_churn"]


# ===========================================================================
# TestAgent Tests
# ===========================================================================

class TestTestAgent:

    def test_perfect_health_low_risk(self):
        result = TestAgent.evaluate(_healthy_test())
        assert result.risk_level == Severity.LOW
        assert result.risk_score <= 0.10
        assert len(result.findings) == 0

    def test_pass_rate_99_5_medium(self):
        m = _healthy_test()
        m["pass_rate_pct"] = 99.5
        m["failed_tests"] = 5
        m["total_tests"] = 1000
        result = TestAgent.evaluate(m)
        assert result.risk_level == Severity.MEDIUM
        failures = [f for f in result.findings if f.category == "TEST_FAILURES"]
        assert len(failures) == 1
        assert failures[0].severity == Severity.MEDIUM

    def test_pass_rate_94_9_high(self):
        m = _healthy_test()
        m["pass_rate_pct"] = 94.9
        m["failed_tests"] = 51
        m["total_tests"] = 1000
        result = TestAgent.evaluate(m)
        failures = [f for f in result.findings if f.category == "TEST_FAILURES"]
        assert failures[0].severity == Severity.HIGH

    def test_pass_rate_89_9_critical(self):
        m = _healthy_test()
        m["pass_rate_pct"] = 89.9
        m["failed_tests"] = 101
        m["total_tests"] = 1000
        result = TestAgent.evaluate(m)
        assert result.risk_level == Severity.CRITICAL
        failures = [f for f in result.findings if f.category == "TEST_FAILURES"]
        assert failures[0].severity == Severity.CRITICAL

    def test_coverage_delta_minus_3_no_finding(self):
        m = _healthy_test()
        m["coverage_delta_pct"] = -3.0
        result = TestAgent.evaluate(m)
        cov = [f for f in result.findings if f.category == "COVERAGE_DROP"]
        assert len(cov) == 0

    def test_coverage_delta_minus_3_1_medium(self):
        m = _healthy_test()
        m["coverage_delta_pct"] = -3.1
        result = TestAgent.evaluate(m)
        cov = [f for f in result.findings if f.category == "COVERAGE_DROP"]
        assert len(cov) == 1
        assert cov[0].severity == Severity.MEDIUM

    def test_coverage_delta_minus_7_1_high(self):
        m = _healthy_test()
        m["coverage_delta_pct"] = -7.1
        result = TestAgent.evaluate(m)
        cov = [f for f in result.findings if f.category == "COVERAGE_DROP"]
        assert cov[0].severity == Severity.HIGH

    def test_flaky_1_medium(self):
        m = _healthy_test()
        m["flaky_tests_count"] = 1
        result = TestAgent.evaluate(m)
        flaky = [f for f in result.findings if f.category == "FLAKY_TESTS"]
        assert len(flaky) == 1
        assert flaky[0].severity == Severity.MEDIUM

    def test_flaky_8_high(self):
        m = _healthy_test()
        m["flaky_tests_count"] = 8
        result = TestAgent.evaluate(m)
        flaky = [f for f in result.findings if f.category == "FLAKY_TESTS"]
        assert flaky[0].severity == Severity.HIGH

    def test_untested_critical_modules_high(self):
        m = _healthy_test()
        m["untested_critical_modules"] = ["auth.py"]
        result = TestAgent.evaluate(m)
        assert result.risk_score >= 0.85
        uncovered = [f for f in result.findings if f.category == "UNTESTED_CRITICAL_PATH"]
        assert len(uncovered) == 1

    def test_worst_case_critical(self):
        m = {
            "total_tests": 1000, "passed_tests": 850, "failed_tests": 150, "skipped_tests": 0,
            "pass_rate_pct": 85.0, "coverage_pct": 60.0, "coverage_delta_pct": -10.0,
            "flaky_tests_count": 15, "duration_seconds": 300.0,
            "untested_critical_modules": ["core.py", "auth.py"]
        }
        result = TestAgent.evaluate(m)
        assert result.risk_level == Severity.CRITICAL

    def test_agent_name(self):
        result = TestAgent.evaluate(_healthy_test())
        assert result.agent_name == "Test Agent"


# ===========================================================================
# DefectAgent Tests
# ===========================================================================

class TestDefectAgent:

    def test_zero_defects_low_risk(self):
        result = DefectAgent.evaluate(_healthy_defect())
        assert result.risk_level == Severity.LOW
        assert result.risk_score <= 0.10
        assert len(result.findings) == 0

    def test_blocker_1_critical(self):
        m = _healthy_defect()
        m["open_blockers"] = 1
        result = DefectAgent.evaluate(m)
        assert result.risk_level == Severity.CRITICAL
        assert result.risk_score >= 0.95
        blocker_findings = [f for f in result.findings if f.category == "BLOCKER_DEFECTS"]
        assert len(blocker_findings) == 1

    def test_blocker_2_critical_still(self):
        m = _healthy_defect()
        m["open_blockers"] = 2
        m["blocker_tickets"] = ["RS-102", "RS-109"]
        result = DefectAgent.evaluate(m)
        assert result.risk_level == Severity.CRITICAL
        assert result.risk_score >= 0.95
        blocker_findings = [f for f in result.findings if f.category == "BLOCKER_DEFECTS"]
        assert "RS-102" in blocker_findings[0].message
        assert "RS-109" in blocker_findings[0].message

    def test_open_critical_1_medium(self):
        m = _healthy_defect()
        m["open_critical"] = 1
        result = DefectAgent.evaluate(m)
        critical_f = [f for f in result.findings if f.category == "CRITICAL_DEFECTS"]
        assert critical_f[0].severity == Severity.MEDIUM

    def test_open_critical_3_high(self):
        m = _healthy_defect()
        m["open_critical"] = 3
        result = DefectAgent.evaluate(m)
        critical_f = [f for f in result.findings if f.category == "CRITICAL_DEFECTS"]
        assert critical_f[0].severity == Severity.HIGH

    def test_density_1_5_no_finding(self):
        m = _healthy_defect()
        m["defect_density_per_kloc"] = 1.5
        result = DefectAgent.evaluate(m)
        density_f = [f for f in result.findings if f.category == "DEFECT_DENSITY"]
        assert len(density_f) == 0

    def test_density_1_51_medium(self):
        m = _healthy_defect()
        m["defect_density_per_kloc"] = 1.51
        result = DefectAgent.evaluate(m)
        density_f = [f for f in result.findings if f.category == "DEFECT_DENSITY"]
        assert len(density_f) == 1
        assert density_f[0].severity == Severity.MEDIUM

    def test_density_2_51_high(self):
        m = _healthy_defect()
        m["defect_density_per_kloc"] = 2.51
        result = DefectAgent.evaluate(m)
        density_f = [f for f in result.findings if f.category == "DEFECT_DENSITY"]
        assert density_f[0].severity == Severity.HIGH

    def test_regression_1_medium(self):
        m = _healthy_defect()
        m["regression_defects"] = 1
        result = DefectAgent.evaluate(m)
        reg = [f for f in result.findings if f.category == "REGRESSION_DEFECTS"]
        assert reg[0].severity == Severity.MEDIUM

    def test_regression_2_high(self):
        m = _healthy_defect()
        m["regression_defects"] = 2
        result = DefectAgent.evaluate(m)
        reg = [f for f in result.findings if f.category == "REGRESSION_DEFECTS"]
        assert reg[0].severity == Severity.HIGH

    def test_blocker_tickets_in_message(self):
        m = _healthy_defect()
        m["open_blockers"] = 1
        m["blocker_tickets"] = ["PROJ-999"]
        result = DefectAgent.evaluate(m)
        blocker_findings = [f for f in result.findings if f.category == "BLOCKER_DEFECTS"]
        assert "PROJ-999" in blocker_findings[0].message

    def test_agent_name(self):
        result = DefectAgent.evaluate(_healthy_defect())
        assert result.agent_name == "Defect Agent"


# ===========================================================================
# OperationsAgent Tests
# ===========================================================================

class TestOperationsAgent:

    def test_perfect_ops_low_risk(self):
        result = OperationsAgent.evaluate(_healthy_ops())
        assert result.risk_level == Severity.LOW
        assert result.risk_score <= 0.10
        assert len(result.findings) == 0

    def test_rollback_1_high(self):
        m = _healthy_ops()
        m["staging_rollbacks_7d"] = 1
        result = OperationsAgent.evaluate(m)
        rb = [f for f in result.findings if f.category == "STAGING_ROLLBACKS"]
        assert len(rb) == 1
        assert rb[0].severity == Severity.HIGH
        assert result.risk_score >= 0.75

    def test_rollback_2_critical(self):
        m = _healthy_ops()
        m["staging_rollbacks_7d"] = 2
        result = OperationsAgent.evaluate(m)
        rb = [f for f in result.findings if f.category == "STAGING_ROLLBACKS"]
        assert rb[0].severity == Severity.CRITICAL
        assert result.risk_score >= 0.85

    def test_pipeline_94_9_medium(self):
        m = _healthy_ops()
        m["pipeline_success_rate_pct"] = 94.9
        result = OperationsAgent.evaluate(m)
        pipe = [f for f in result.findings if f.category == "PIPELINE_INSTABILITY"]
        assert pipe[0].severity == Severity.MEDIUM

    def test_pipeline_79_9_high(self):
        m = _healthy_ops()
        m["pipeline_success_rate_pct"] = 79.9
        result = OperationsAgent.evaluate(m)
        pipe = [f for f in result.findings if f.category == "PIPELINE_INSTABILITY"]
        assert pipe[0].severity == Severity.HIGH

    def test_infra_drift_high(self):
        m = _healthy_ops()
        m["infra_config_drift"] = True
        result = OperationsAgent.evaluate(m)
        drift = [f for f in result.findings if f.category == "INFRA_DRIFT"]
        assert len(drift) == 1
        assert drift[0].severity == Severity.HIGH
        assert result.risk_score >= 0.70

    def test_error_budget_exactly_20_no_finding(self):
        m = _healthy_ops()
        m["error_budget_burn_pct"] = 20.0
        result = OperationsAgent.evaluate(m)
        perf = [f for f in result.findings if f.category == "PERFORMANCE_DEGRADATION"]
        assert len(perf) == 0

    def test_error_budget_20_1_high(self):
        m = _healthy_ops()
        m["error_budget_burn_pct"] = 20.1
        result = OperationsAgent.evaluate(m)
        perf = [f for f in result.findings if f.category == "PERFORMANCE_DEGRADATION"]
        assert len(perf) == 1
        assert perf[0].severity == Severity.HIGH

    def test_latency_100_no_finding(self):
        m = _healthy_ops()
        m["p95_latency_delta_ms"] = 100.0
        result = OperationsAgent.evaluate(m)
        perf = [f for f in result.findings if f.category == "PERFORMANCE_DEGRADATION"]
        assert len(perf) == 0

    def test_latency_100_1_high(self):
        m = _healthy_ops()
        m["p95_latency_delta_ms"] = 100.1
        result = OperationsAgent.evaluate(m)
        perf = [f for f in result.findings if f.category == "PERFORMANCE_DEGRADATION"]
        assert len(perf) == 1

    def test_staging_status_in_summary(self):
        m = _healthy_ops()
        m["staging_deploy_status"] = "DEGRADED"
        result = OperationsAgent.evaluate(m)
        assert "DEGRADED" in result.summary

    def test_agent_name(self):
        result = OperationsAgent.evaluate(_healthy_ops())
        assert result.agent_name == "Operations Agent"
