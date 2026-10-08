export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
export type Trend = 'INCREASING' | 'DECREASING' | 'STABLE' | 'UNKNOWN';

export interface RiskFinding {
  category: string;
  severity: Severity;
  score: number;
  message: string;
  evidence: Record<string, any>;
}

export interface GitMetrics {
  commit_count: number;
  files_changed: number;
  lines_added: number;
  lines_deleted: number;
  code_churn: number;
  unique_contributors: number;
  pr_count: number;
}

export interface RiskReport {
  repository: string;
  release: string;
  risk_score: number;
  risk_level: Severity;
  confidence: number;
  trend: Trend;
  summary: string;
  metrics: GitMetrics;
  findings: RiskFinding[];
  recommendations: string[];
  explanation: string;
}

export interface ReleaseRequest {
  repository: string;
  release: string;
  historical_window?: number;
}
