from typing import Dict, Any, List
from app.schemas.unified_risk import AgentResult, Severity, RiskFinding, DefectMetrics

class DefectAgent:
    """
    Defect Domain Agent.
    Evaluates open blocker/critical defects, defect density, bug escape rates,
    and regression bugs from issue tracking telemetry.
    """
    @staticmethod
    def evaluate(metrics_dict: Dict[str, Any]) -> AgentResult:
        metrics = DefectMetrics(**metrics_dict)
        findings: List[RiskFinding] = []
        score = 0.05 # Base clean score
        
        # 1. Open Blocker Defects (P0 HARD GATE)
        if metrics.open_blockers > 0:
            score = max(score, 0.95)
            tickets = ", ".join(metrics.blocker_tickets) if metrics.blocker_tickets else f"{metrics.open_blockers} tickets"
            findings.append(RiskFinding(
                category="BLOCKER_DEFECTS",
                severity=Severity.CRITICAL,
                score=0.95,
                message=f"HARD RELEASE GATE: {metrics.open_blockers} unresolved BLOCKER defect(s) detected: {tickets}.",
                evidence={"open_blockers": metrics.open_blockers, "tickets": metrics.blocker_tickets}
            ))
            
        # 2. Open Critical Defects
        if metrics.open_critical > 0:
            sev = Severity.HIGH if metrics.open_critical >= 3 else Severity.MEDIUM
            score = max(score, 0.75 if sev == Severity.HIGH else 0.50)
            findings.append(RiskFinding(
                category="CRITICAL_DEFECTS",
                severity=sev,
                score=score,
                message=f"{metrics.open_critical} open P1 Critical defects pending resolution.",
                evidence={"open_critical": metrics.open_critical}
            ))
            
        # 3. Defect Density (>1.5 per KLOC is concerning)
        if metrics.defect_density_per_kloc > 1.5:
            sev = Severity.HIGH if metrics.defect_density_per_kloc > 2.5 else Severity.MEDIUM
            score = max(score, 0.70 if sev == Severity.HIGH else 0.45)
            findings.append(RiskFinding(
                category="DEFECT_DENSITY",
                severity=sev,
                score=score,
                message=f"High defect density ({metrics.defect_density_per_kloc:.2f} defects/KLOC, baseline threshold: 1.0).",
                evidence={"defect_density": metrics.defect_density_per_kloc}
            ))
            
        # 4. Regression Defects
        if metrics.regression_defects > 0:
            sev = Severity.HIGH if metrics.regression_defects >= 2 else Severity.MEDIUM
            score = max(score, 0.75 if sev == Severity.HIGH else 0.45)
            findings.append(RiskFinding(
                category="REGRESSION_DEFECTS",
                severity=sev,
                score=score,
                message=f"{metrics.regression_defects} regression defect(s) identified in pre-release testing.",
                evidence={"regression_defects": metrics.regression_defects}
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
            
        summary = f"Defect risk is {level.value} (score: {score:.2f}). {metrics.open_blockers} blockers and {metrics.open_critical} critical defects open."
        
        return AgentResult(
            agent_name="Defect Agent",
            risk_score=round(score, 2),
            risk_level=level,
            confidence=0.95,
            summary=summary,
            metrics=metrics.model_dump(),
            findings=findings
        )
