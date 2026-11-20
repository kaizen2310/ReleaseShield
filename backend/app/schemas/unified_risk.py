from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskTrend(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"

class ReleaseType(str, Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    PATCH = "PATCH"
    HOTFIX = "HOTFIX"

class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"

class ActionPriority(str, Enum):
    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ActionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    WAIVED = "WAIVED"

class RiskFinding(BaseModel):
    category: str
    severity: Severity
    score: float
    message: str
    evidence: Dict[str, Any] = Field(default_factory=dict)

# Domain Metrics
class CodeMetrics(BaseModel):
    commit_count: int = 0
    files_changed: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    code_churn: int = 0
    unique_contributors: int = 0
    pr_count: int = 0
    avg_pr_merge_time_hours: float = 0.0
    high_risk_files_touched: int = 0

class TestMetrics(BaseModel):
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    pass_rate_pct: float = 100.0
    coverage_pct: float = 85.0
    coverage_delta_pct: float = 0.0
    flaky_tests_count: int = 0
    duration_seconds: float = 0.0
    untested_critical_modules: List[str] = Field(default_factory=list)

class DefectMetrics(BaseModel):
    open_blockers: int = 0
    open_critical: int = 0
    open_major: int = 0
    defect_density_per_kloc: float = 0.0
    bug_escape_rate_pct: float = 0.0
    regression_defects: int = 0
    mttr_hours: float = 0.0
    blocker_tickets: List[str] = Field(default_factory=list)

class OperationsMetrics(BaseModel):
    pipeline_success_rate_pct: float = 100.0
    recent_failed_pipelines: int = 0
    staging_deploy_status: str = "HEALTHY" # HEALTHY, DEGRADED, FAILED
    staging_rollbacks_7d: int = 0
    infra_config_drift: bool = False
    p95_latency_delta_ms: float = 0.0
    error_budget_burn_pct: float = 0.0

class AgentResult(BaseModel):
    agent_name: str
    risk_score: float
    risk_level: Severity
    confidence: float
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    findings: List[RiskFinding] = Field(default_factory=list)

class RiskDriver(BaseModel):
    feature_name: str
    display_name: str
    importance_score: float
    current_value: Any
    baseline_value: Any
    contribution_pct: float
    impact_level: str # HIGH, MEDIUM, LOW
    description: str

class RequiredAction(BaseModel):
    id: str
    title: str
    description: str
    priority: ActionPriority
    category: str # CODE, TEST, DEFECT, OPERATIONS, GOVERNANCE
    owner_role: str # QA Lead, Security Architect, Release Manager, DevOps Lead
    status: ActionStatus = ActionStatus.PENDING
    waiver_reason: Optional[str] = None

class HumanApprovalDetails(BaseModel):
    status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    approver_name: Optional[str] = None
    approver_role: Optional[str] = None
    notes: Optional[str] = None
    timestamp: Optional[str] = None
    deployment_blocked: bool = True # Deployment is strictly manual / human-gated

class HybridEngineBreakdown(BaseModel):
    xgboost_risk_score: float
    deterministic_rule_score: float
    blended_risk_score: float
    hard_gate_triggered: bool = False
    hard_gate_reason: Optional[str] = None
    model_version: str = "XGBoost v3.4 + Deterministic Rules"

class UnifiedRiskReport(BaseModel):
    repository: str
    release: str
    release_type: ReleaseType = ReleaseType.MINOR
    target_environment: str = "production"
    scenario: str = "standard_healthy"
    
    risk_score: float
    risk_level: Severity
    confidence: float
    trend: RiskTrend
    summary: str
    
    hybrid_engine: HybridEngineBreakdown
    risk_drivers: List[RiskDriver] = Field(default_factory=list)
    
    code_agent: AgentResult
    test_agent: AgentResult
    defect_agent: AgentResult
    operations_agent: AgentResult
    
    recommendations: List[str] = Field(default_factory=list)
    required_actions: List[RequiredAction] = Field(default_factory=list)
    explanation: str = ""
    approval: HumanApprovalDetails = Field(default_factory=HumanApprovalDetails)

class ReleaseAnalysisRequest(BaseModel):
    repository: str
    release: str
    historical_window: int = 10
    release_type: ReleaseType = ReleaseType.MINOR
    target_environment: str = "production"
    scenario: str = "standard_healthy"
    custom_test_metrics: Optional[Dict[str, Any]] = None
    custom_defect_metrics: Optional[Dict[str, Any]] = None
    custom_operations_metrics: Optional[Dict[str, Any]] = None

class ApprovalSubmissionRequest(BaseModel):
    repository: str
    release: str
    status: ApprovalStatus
    approver_name: str
    approver_role: str
    notes: Optional[str] = ""

class ActionToggleRequest(BaseModel):
    repository: str
    release: str
    action_id: str
    status: ActionStatus
    waiver_reason: Optional[str] = None
