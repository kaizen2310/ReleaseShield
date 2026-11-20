from typing import List, Tuple
from app.schemas.unified_risk import (
    AgentResult, RequiredAction, ActionPriority, ActionStatus
)

class RecommendationEngine:
    """
    Generates practical, release-readiness actions and a structured required-actions checklist.
    Strictly avoids generic AI text like 'ensure code is tested'; provides concrete operational steps.
    """
    @classmethod
    def generate(
        cls,
        code_result: AgentResult,
        test_result: AgentResult,
        defect_result: AgentResult,
        ops_result: AgentResult,
        risk_level: str
    ) -> Tuple[List[str], List[RequiredAction]]:
        
        recommendations: List[str] = []
        actions: List[RequiredAction] = []
        act_counter = 1
        
        # 1. Defect Actions (Priority: BLOCKER / HIGH)
        d_m = defect_result.metrics
        if d_m.get("open_blockers", 0) > 0:
            tickets = ", ".join(d_m.get("blocker_tickets", []))
            rec_text = f"Resolve {d_m.get('open_blockers')} open BLOCKER ticket(s) ({tickets}) or obtain a formal VP of Engineering risk waiver."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-DEF-{act_counter:02d}",
                title=f"Resolve {d_m.get('open_blockers')} Blocker Defect(s)",
                description=f"Tickets requiring resolution or signed release waiver: {tickets}.",
                priority=ActionPriority.BLOCKER,
                category="DEFECT",
                owner_role="QA Lead / Tech Lead",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if d_m.get("open_critical", 0) >= 3:
            rec_text = f"Triage {d_m.get('open_critical')} P1 Critical bugs in release triage meeting; defer non-essential fixes to next minor cycle."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-DEF-{act_counter:02d}",
                title="Triage P1 Critical Defects",
                description="Conduct risk review for high-impact open defects with Product Owner.",
                priority=ActionPriority.HIGH,
                category="DEFECT",
                owner_role="Engineering Manager",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        # 2. Test Actions (Priority: BLOCKER / HIGH)
        t_m = test_result.metrics
        if t_m.get("pass_rate_pct", 100.0) < 95.0:
            rec_text = f"Fix {t_m.get('failed_tests')} failing automated tests and verify 100% green build in staging CI."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-TST-{act_counter:02d}",
                title="Re-run and Fix Failing Tests",
                description=f"{t_m.get('failed_tests')} tests currently failing in the test suite.",
                priority=ActionPriority.BLOCKER if t_m.get("pass_rate_pct") < 90.0 else ActionPriority.HIGH,
                category="TEST",
                owner_role="QA Lead",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if t_m.get("coverage_delta_pct", 0.0) < -3.0:
            rec_text = f"Add missing unit tests to compensate for {abs(t_m.get('coverage_delta_pct')):.1f}% coverage regression (current coverage: {t_m.get('coverage_pct'):.1f}%)."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-TST-{act_counter:02d}",
                title="Restore Test Coverage Baseline",
                description=f"Add unit test assertions for new code paths to meet minimum 80% coverage threshold.",
                priority=ActionPriority.HIGH,
                category="TEST",
                owner_role="Software Engineers",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if t_m.get("flaky_tests_count", 0) > 0:
            rec_text = f"Quarantine or stabilize {t_m.get('flaky_tests_count')} flaky tests to prevent false build confidence."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-TST-{act_counter:02d}",
                title="Isolate Flaky Tests",
                description="Tag flaky tests with @quarantine so production deployment gate is deterministic.",
                priority=ActionPriority.MEDIUM,
                category="TEST",
                owner_role="SDET / QA Automation",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        # 3. Operations Actions
        o_m = ops_result.metrics
        if o_m.get("staging_rollbacks_7d", 0) > 0:
            rec_text = f"Conduct post-mortem on {o_m.get('staging_rollbacks_7d')} staging rollback(s) and test database down-migration scripts in isolated sandbox."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-OPS-{act_counter:02d}",
                title="Verify Rollback & Migration Runbooks",
                description="Dry-run database schema rollback scripts in Staging environment.",
                priority=ActionPriority.HIGH,
                category="OPERATIONS",
                owner_role="DevOps Lead / SRE",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if o_m.get("infra_config_drift", False):
            rec_text = "Synchronize Terraform / Helm chart variables between Staging and Production to eliminate configuration drift."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-OPS-{act_counter:02d}",
                title="Reconcile Infrastructure Config Drift",
                description="Verify environment parity between staging and production clusters.",
                priority=ActionPriority.HIGH,
                category="OPERATIONS",
                owner_role="Platform Engineer",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if o_m.get("pipeline_success_rate_pct", 100.0) < 90.0:
            rec_text = "Ensure 2 consecutive green CI/CD deployment runs before promoting release artifact."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-OPS-{act_counter:02d}",
                title="Validate CI/CD Pipeline Stability",
                description="Run full end-to-end integration pipeline cleanly twice in staging.",
                priority=ActionPriority.MEDIUM,
                category="OPERATIONS",
                owner_role="Release Engineer",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        # 4. Code & Governance Actions
        c_m = code_result.metrics
        if c_m.get("high_risk_files_touched", 0) >= 5 or c_m.get("code_churn", 0) > 6000:
            rec_text = f"Require secondary senior architectural review on {c_m.get('high_risk_files_touched')} core/security files before release tag approval."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-COD-{act_counter:02d}",
                title="Secondary Code Owner Review",
                description=f"Approve pull requests touching critical architecture and configuration files.",
                priority=ActionPriority.HIGH,
                category="CODE",
                owner_role="Principal Architect",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        if c_m.get("avg_pr_merge_time_hours", 24.0) < 4.0 and c_m.get("pr_count", 0) > 0:
            rec_text = "Verify that expedited PRs received thorough code review and did not bypass required branch protection rules."
            recommendations.append(rec_text)
            actions.append(RequiredAction(
                id=f"ACT-COD-{act_counter:02d}",
                title="Audit Fast-Tracked PRs",
                description="Confirm all fast-tracked pull requests have passing automated CI checks and peer approvals.",
                priority=ActionPriority.MEDIUM,
                category="GOVERNANCE",
                owner_role="Release Manager",
                status=ActionStatus.PENDING
            ))
            act_counter += 1
            
        # Always include Mandatory Human Approval Action Gate
        actions.append(RequiredAction(
            id=f"ACT-GOV-{act_counter:02d}",
            title="Mandatory Human Gatekeeper Sign-Off",
            description="Obtain formal sign-off from authorized Release Manager or Tech Lead before proceeding.",
            priority=ActionPriority.BLOCKER if risk_level in ["CRITICAL", "HIGH"] else ActionPriority.HIGH,
            category="GOVERNANCE",
            owner_role="Release Manager",
            status=ActionStatus.PENDING
        ))
        
        if not recommendations:
            recommendations.append("All release telemetry is within nominal parameters. Follow standard canary deployment procedure.")
            
        return recommendations, actions
