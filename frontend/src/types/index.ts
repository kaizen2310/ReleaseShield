export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Trend = 'INCREASING' | 'DECREASING' | 'STABLE' | 'UNKNOWN';
export type ReleaseType = 'MAJOR' | 'MINOR' | 'PATCH' | 'HOTFIX';
export type ApprovalStatus = 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED';
export type ActionPriority = 'BLOCKER' | 'HIGH' | 'MEDIUM' | 'LOW';
export type ActionStatus = 'PENDING' | 'COMPLETED' | 'WAIVED';

export interface RiskFinding {
  category: string;
  severity: Severity;
  score: number;
  message: string;
  evidence: Record<string, any>;
}

export interface RiskDriver {
  feature_name: string;
  display_name: string;
  importance_score: number;
  current_value: any;
  baseline_value: any;
  contribution_pct: number;
  impact_level: 'HIGH' | 'MEDIUM' | 'LOW';
  description: string;
}

export interface RequiredAction {
  id: string;
  title: string;
  description: string;
  priority: ActionPriority;
  category: string;
  owner_role: string;
  status: ActionStatus;
  waiver_reason?: string;
}

export interface AgentResult {
  agent_name: string;
  risk_score: number;
  risk_level: Severity;
  confidence: number;
  summary: string;
  metrics: Record<string, any>;
  findings: RiskFinding[];
}

export interface HybridEngineBreakdown {
  xgboost_risk_score: number;
  deterministic_rule_score: number;
  blended_risk_score: number;
  hard_gate_triggered: boolean;
  hard_gate_reason?: string;
  model_version: string;
}

export interface HumanApprovalDetails {
  status: ApprovalStatus;
  approver_name?: string;
  approver_role?: string;
  notes?: string;
  timestamp?: string;
  deployment_blocked: boolean;
}

export interface UnifiedRiskReport {
  repository: string;
  release: string;
  release_type: ReleaseType;
  target_environment: string;
  scenario: string;
  
  risk_score: number;
  risk_level: Severity;
  confidence: number;
  trend: Trend;
  summary: string;
  
  hybrid_engine: HybridEngineBreakdown;
  risk_drivers: RiskDriver[];
  
  code_agent: AgentResult;
  test_agent: AgentResult;
  defect_agent: AgentResult;
  operations_agent: AgentResult;
  
  recommendations: string[];
  required_actions: RequiredAction[];
  explanation: string;
  approval: HumanApprovalDetails;
  
  // Backward compatibility fields
  metrics?: Record<string, any>;
  findings?: RiskFinding[];
}

export interface ReleaseAnalysisRequest {
  repository: string;
  release: string;
  historical_window?: number;
  release_type?: ReleaseType;
  target_environment?: string;
  scenario?: string;
  custom_test_metrics?: Record<string, any>;
  custom_defect_metrics?: Record<string, any>;
  custom_operations_metrics?: Record<string, any>;
}

export interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  expected_risk: Severity;
}

export interface ApprovalSubmissionRequest {
  repository: string;
  release: string;
  status: ApprovalStatus;
  approver_name: string;
  approver_role: string;
  notes?: string;
}

export interface ActionToggleRequest {
  repository: string;
  release: string;
  action_id: string;
  status: ActionStatus;
  waiver_reason?: string;
}
