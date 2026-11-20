from typing import Dict, Any, List
from app.schemas.unified_risk import AgentResult, Severity, RiskFinding, CodeMetrics

class CodeAgent:
    """
    Code / Git Domain Agent.
    Evaluates code churn, commit velocity, PR review patterns, and sensitive file changes
    using deterministic threshold and baseline anomaly rules.
    """
    @staticmethod
    def evaluate(metrics_dict: Dict[str, Any], baseline_comparison: Dict[str, Any] = None) -> AgentResult:
        metrics = CodeMetrics(**metrics_dict)
        findings: List[RiskFinding] = []
        score = 0.10 # Base clean score
        
        # 1. Code Churn Anomaly
        if metrics.code_churn > 5000:
            sev = Severity.HIGH if metrics.code_churn > 8000 else Severity.MEDIUM
            score = max(score, 0.80 if sev == Severity.HIGH else 0.55)
            findings.append(RiskFinding(
                category="CODE_CHURN",
                severity=sev,
                score=score,
                message=f"Abnormally high code churn ({metrics.code_churn:,} total lines modified).",
                evidence={"code_churn": metrics.code_churn, "threshold": 5000}
            ))
            
        # 2. Files Changed (Broad blast radius)
        if metrics.files_changed > 80:
            sev = Severity.HIGH if metrics.files_changed > 120 else Severity.MEDIUM
            score = max(score, 0.70 if sev == Severity.HIGH else 0.50)
            findings.append(RiskFinding(
                category="CHANGE_SCOPE",
                severity=sev,
                score=score,
                message=f"Expansive change blast radius: {metrics.files_changed} files modified.",
                evidence={"files_changed": metrics.files_changed, "threshold": 80}
            ))
            
        # 3. Rushed PR Reviews
        if metrics.pr_count > 0 and metrics.avg_pr_merge_time_hours < 4.0:
            score = max(score, 0.65)
            findings.append(RiskFinding(
                category="RUSHED_PR_REVIEW",
                severity=Severity.HIGH,
                score=0.65,
                message=f"Rushed PR merge velocity (average merge time {metrics.avg_pr_merge_time_hours:.1f} hours). Risk of insufficient peer review.",
                evidence={"avg_pr_merge_time_hours": metrics.avg_pr_merge_time_hours, "threshold_min": 4.0}
            ))
            
        # 4. High Risk File Modifications (security, migrations, auth, configs)
        if metrics.high_risk_files_touched >= 5:
            sev = Severity.HIGH if metrics.high_risk_files_touched >= 10 else Severity.MEDIUM
            score = max(score, 0.75 if sev == Severity.HIGH else 0.50)
            findings.append(RiskFinding(
                category="CRITICAL_COMPONENTS",
                severity=sev,
                score=score,
                message=f"{metrics.high_risk_files_touched} core/security/infrastructure files modified in this release.",
                evidence={"high_risk_files_touched": metrics.high_risk_files_touched}
            ))
            
        # Determine Severity Level
        if score >= 0.75:
            level = Severity.HIGH
        elif score >= 0.40:
            level = Severity.MEDIUM
        else:
            level = Severity.LOW
            
        summary = f"Code risk is {level.value} (score: {score:.2f}). {len(findings)} code anomalies detected."
        
        return AgentResult(
            agent_name="Code / Git Agent",
            risk_score=round(score, 2),
            risk_level=level,
            confidence=0.90,
            summary=summary,
            metrics=metrics.model_dump(),
            findings=findings
        )
