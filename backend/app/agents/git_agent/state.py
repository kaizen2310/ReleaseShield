from typing import TypedDict, Optional, List, Dict, Any
from app.schemas.metrics import GitMetrics
from app.schemas.risk import BaselineAnalysis, RiskAssessment, RiskFinding, RiskTrend, Severity

class GitAgentState(TypedDict, total=False):
    # Inputs
    repository: str
    target_release: str
    historical_window: int
    
    # Internal Data Flow
    previous_release: str
    release_metadata: Dict[str, Any]
    commits: List[Dict[str, Any]]
    pull_requests: List[Dict[str, Any]]
    changed_files: List[Dict[str, Any]]
    
    # Processed Data
    current_metrics: Optional[GitMetrics]
    historical_metrics: List[Any] # from DB
    baseline_analysis: Optional[BaselineAnalysis]
    
    # Risk Engine Outputs
    risk_signals: List[RiskFinding]
    risk_score: float
    risk_level: Severity
    trend: RiskTrend
    confidence: float
    
    # Final outputs
    findings: List[RiskFinding]
    recommendations: List[str]
    llm_explanation: str
    
    # Error handling
    error: str
    retries: int
    critic_feedback: str
