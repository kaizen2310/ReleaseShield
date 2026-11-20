from typing import Dict, Any, List
from app.schemas.unified_risk import AgentResult, Severity, RiskFinding, OperationsMetrics

class OperationsAgent:
    """
    Operations & Deployment Domain Agent.
    Evaluates CI/CD pipeline reliability, staging deployment health, rollback frequency,
    infrastructure configuration drift, and performance latency deltas.
    """
    @staticmethod
    def evaluate(metrics_dict: Dict[str, Any]) -> AgentResult:
        metrics = OperationsMetrics(**metrics_dict)
        findings: List[RiskFinding] = []
        score = 0.05 # Base clean score
        
        # 1. Staging Rollbacks (High operational warning)
        if metrics.staging_rollbacks_7d > 0:
            sev = Severity.CRITICAL if metrics.staging_rollbacks_7d >= 2 else Severity.HIGH
            score = max(score, 0.90 if sev == Severity.CRITICAL else 0.75)
            findings.append(RiskFinding(
                category="STAGING_ROLLBACKS",
                severity=sev,
                score=score,
                message=f"{metrics.staging_rollbacks_7d} deployment rollback(s) occurred in staging within the last 7 days.",
                evidence={"staging_rollbacks": metrics.staging_rollbacks_7d}
            ))
            
        # 2. CI/CD Pipeline Success Rate
        if metrics.pipeline_success_rate_pct < 95.0:
            if metrics.pipeline_success_rate_pct < 80.0:
                sev = Severity.HIGH
                score = max(score, 0.80)
            else:
                sev = Severity.MEDIUM
                score = max(score, 0.50)
            findings.append(RiskFinding(
                category="PIPELINE_INSTABILITY",
                severity=sev,
                score=score,
                message=f"CI/CD pipeline success rate degraded to {metrics.pipeline_success_rate_pct:.1f}% ({metrics.recent_failed_pipelines} recent failures).",
                evidence={"pipeline_success_rate": metrics.pipeline_success_rate_pct, "failed_pipelines": metrics.recent_failed_pipelines}
            ))
            
        # 3. Infrastructure Configuration Drift
        if metrics.infra_config_drift:
            score = max(score, 0.70)
            findings.append(RiskFinding(
                category="INFRA_DRIFT",
                severity=Severity.HIGH,
                score=0.70,
                message="Unreconciled infrastructure or configuration drift detected between Staging and Production.",
                evidence={"infra_config_drift": True}
            ))
            
        # 4. Latency / Error Budget Burn
        if metrics.error_budget_burn_pct > 20.0 or metrics.p95_latency_delta_ms > 100.0:
            score = max(score, 0.75)
            findings.append(RiskFinding(
                category="PERFORMANCE_DEGRADATION",
                severity=Severity.HIGH,
                score=0.75,
                message=f"Performance regression: P95 latency increased by {metrics.p95_latency_delta_ms:+.1f}ms; error budget burn at {metrics.error_budget_burn_pct:.1f}%.",
                evidence={"latency_delta_ms": metrics.p95_latency_delta_ms, "error_budget_burn_pct": metrics.error_budget_burn_pct}
            ))
            
        # Overall Agent Risk Level
        if score >= 0.85:
            level = Severity.CRITICAL
        elif score >= 0.60:
            level = Severity.HIGH
        elif score >= 0.30:
            level = Severity.MEDIUM
        else:
            level = Severity.LOW
            
        summary = f"Operations risk is {level.value} (score: {score:.2f}). Pipeline success rate is {metrics.pipeline_success_rate_pct:.1f}%, staging status: {metrics.staging_deploy_status}."
        
        return AgentResult(
            agent_name="Operations Agent",
            risk_score=round(score, 2),
            risk_level=level,
            confidence=0.92,
            summary=summary,
            metrics=metrics.model_dump(),
            findings=findings
        )
