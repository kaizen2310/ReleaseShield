from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from enum import Enum

class BaselineStatistic(BaseModel):
    feature: str
    current: float
    historical_mean: float
    historical_median: float
    minimum: float
    maximum: float
    standard_deviation: float
    ratio: float
    deviation_from_mean: float
    z_score: float

class BaselineAnalysis(BaseModel):
    repository: str
    target_release: str
    historical_releases_count: int
    features: List[BaselineStatistic]

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RiskFinding(BaseModel):
    category: str
    severity: Severity
    score: float
    message: str
    evidence: Dict[str, Any]

class RiskTrend(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    UNKNOWN = "UNKNOWN"

class RiskAssessment(BaseModel):
    repository: str
    release: str
    risk_score: float
    risk_level: Severity
    confidence: float
    trend: RiskTrend
    findings: List[RiskFinding]
