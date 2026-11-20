from typing import Dict, Any, List
from app.schemas.unified_risk import AgentResult, Severity, RiskFinding, TestMetrics

class TestAgent:
    """
    Test Domain Agent.
    Evaluates test suite health, pass rates, code coverage deltas, flaky tests,
    and untested critical modules using deterministic QA gates.
    """
    @staticmethod
    def evaluate(metrics_dict: Dict[str, Any]) -> AgentResult:
        metrics = TestMetrics(**metrics_dict)
        findings: List[RiskFinding] = []
        score = 0.05 # Base clean score
        
        # 1. Test Pass Rate Hard Gate
        if metrics.pass_rate_pct < 100.0:
            if metrics.pass_rate_pct < 95.0:
                sev = Severity.CRITICAL if metrics.pass_rate_pct < 90.0 else Severity.HIGH
                score = max(score, 0.90 if sev == Severity.CRITICAL else 0.75)
            else:
                sev = Severity.MEDIUM
                score = max(score, 0.45)
                
            findings.append(RiskFinding(
                category="TEST_FAILURES",
                severity=sev,
                score=score,
                message=f"Test pass rate is {metrics.pass_rate_pct:.1f}% ({metrics.failed_tests} failing tests out of {metrics.total_tests}).",
                evidence={"pass_rate_pct": metrics.pass_rate_pct, "failed_tests": metrics.failed_tests, "total_tests": metrics.total_tests}
            ))
            
        # 2. Coverage Drop Anomaly
        if metrics.coverage_delta_pct < -3.0:
            sev = Severity.HIGH if metrics.coverage_delta_pct < -7.0 else Severity.MEDIUM
            score = max(score, 0.80 if sev == Severity.HIGH else 0.55)
            findings.append(RiskFinding(
                category="COVERAGE_DROP",
                severity=sev,
                score=score,
                message=f"Test coverage dropped by {abs(metrics.coverage_delta_pct):.1f}% (current coverage: {metrics.coverage_pct:.1f}%).",
                evidence={"coverage_delta_pct": metrics.coverage_delta_pct, "coverage_pct": metrics.coverage_pct}
            ))
            
        # 3. Flaky Tests
        if metrics.flaky_tests_count > 0:
            sev = Severity.HIGH if metrics.flaky_tests_count >= 8 else Severity.MEDIUM
            score = max(score, 0.65 if sev == Severity.HIGH else 0.40)
            findings.append(RiskFinding(
                category="FLAKY_TESTS",
                severity=sev,
                score=score,
                message=f"{metrics.flaky_tests_count} flaky tests detected, undermining CI build confidence.",
                evidence={"flaky_tests_count": metrics.flaky_tests_count}
            ))
            
        # 4. Untested Critical Modules
        if metrics.untested_critical_modules:
            score = max(score, 0.85)
            modules_list = ", ".join(metrics.untested_critical_modules)
            findings.append(RiskFinding(
                category="UNTESTED_CRITICAL_PATH",
                severity=Severity.HIGH,
                score=0.85,
                message=f"Critical modules touched without test coverage: {modules_list}.",
                evidence={"untested_modules": metrics.untested_critical_modules}
            ))
            
        # Overall Agent Risk Level
        if score >= 0.80:
            level = Severity.CRITICAL
        elif score >= 0.60:
            level = Severity.HIGH
        elif score >= 0.35:
            level = Severity.MEDIUM
        else:
            level = Severity.LOW
            
        summary = f"Test risk is {level.value} (score: {score:.2f}). Pass rate is {metrics.pass_rate_pct:.1f}% with {metrics.flaky_tests_count} flaky tests."
        
        return AgentResult(
            agent_name="Test Agent",
            risk_score=round(score, 2),
            risk_level=level,
            confidence=0.95,
            summary=summary,
            metrics=metrics.model_dump(),
            findings=findings
        )
