from typing import List, Dict, Any, Optional
from app.schemas.risk import BaselineAnalysis, BaselineStatistic, RiskFinding, Severity, RiskAssessment, RiskTrend

class RiskService:
    # ---------------------------------------------------------
    # Configurable thresholds and weights for MVP
    # ---------------------------------------------------------
    WEIGHTS = {
        "CODE_CHURN": 0.25,
        "CHANGE_SCOPE": 0.20,
        "COMMIT_ACTIVITY": 0.20,
        "PR_ACTIVITY": 0.15,
        "CONTRIBUTOR_ACTIVITY": 0.10,
        "DEPENDENCY_CHANGES": 0.10
    }

    # Threshold ratios (current / historical_mean)
    THRESHOLDS = {
        "HIGH_RATIO": 2.0,     # > 200% of historical average
        "MEDIUM_RATIO": 1.5,   # > 150% of historical average
        "LOW_RATIO": 1.2       # > 120% of historical average
    }

    # Overall Risk Score thresholds
    RISK_LEVELS = {
        "HIGH": 0.60,
        "MEDIUM": 0.30
    }

    @staticmethod
    def _calculate_feature_risk(stat: BaselineStatistic, category_name: str, msg_prefix: str) -> Optional[RiskFinding]:
        """Evaluates a single feature statistic against thresholds (z-score and ratio) to generate a risk finding."""
        
        # If both are zero, it's normal
        if stat.current == 0 and stat.historical_mean == 0:
            return None
            
        severity = Severity.LOW
        score = 0.25
        
        # Use z-score if available and standard deviation is meaningful
        if stat.standard_deviation > 0:
            if stat.z_score >= 3.0:
                severity = Severity.HIGH
                score = 0.85
            elif stat.z_score >= 2.0:
                severity = Severity.MEDIUM
                score = 0.55
            elif stat.z_score < 1.0 and stat.ratio < RiskService.THRESHOLDS["LOW_RATIO"]:
                return None
        else:
            # Fallback to ratio
            if stat.ratio >= RiskService.THRESHOLDS["HIGH_RATIO"] or (stat.historical_mean == 0 and stat.current > 0):
                severity = Severity.HIGH
                score = 0.85
            elif stat.ratio >= RiskService.THRESHOLDS["MEDIUM_RATIO"]:
                severity = Severity.MEDIUM
                score = 0.55
            elif stat.ratio < RiskService.THRESHOLDS["LOW_RATIO"]:
                return None

        # Build evidence message
        if stat.standard_deviation > 0:
            msg = f"{msg_prefix} (Z-score: {stat.z_score:.2f}, {stat.ratio:.2f}x historical average)."
        else:
            msg = f"{msg_prefix} ({stat.ratio:.2f}x historical average)."

        return RiskFinding(
            category=category_name,
            severity=severity,
            score=score,
            message=msg,
            evidence={
                "current": stat.current,
                "historical_mean": stat.historical_mean,
                "historical_std": stat.standard_deviation,
                "ratio": stat.ratio,
                "z_score": stat.z_score
            }
        )

    @staticmethod
    def analyze_anomalies(baseline: BaselineAnalysis) -> List[RiskFinding]:
        findings = []
        
        feature_map = {f.feature: f for f in baseline.features}
        
        # Code Churn
        if "code_churn" in feature_map:
            finding = RiskService._calculate_feature_risk(
                feature_map["code_churn"], 
                "CODE_CHURN", 
                "Code churn is significantly above historical baseline"
            )
            if finding: findings.append(finding)
            
        # Change Scope
        if "files_changed" in feature_map:
            finding = RiskService._calculate_feature_risk(
                feature_map["files_changed"], 
                "CHANGE_SCOPE", 
                "Number of files changed is abnormally high"
            )
            if finding: findings.append(finding)
            
        # Commit Activity
        if "commits_per_day" in feature_map:
            finding = RiskService._calculate_feature_risk(
                feature_map["commits_per_day"], 
                "COMMIT_ACTIVITY", 
                "Commit velocity leading up to this release is unusually high"
            )
            if finding: findings.append(finding)
            
        # PR Activity
        if "avg_pr_merge_time_hours" in feature_map:
            finding = RiskService._calculate_feature_risk(
                feature_map["avg_pr_merge_time_hours"], 
                "PR_ACTIVITY", 
                "Pull requests took longer to merge than usual, indicating potential complexity"
            )
            if finding: findings.append(finding)
            
        # Contributor Activity (Fix Phase 2.4)
        if "unique_contributors" in feature_map:
            # We want to flag if contributors DROP significantly, so we invert the logic slightly,
            # or we flag if new contributors spike. Let's just flag a spike for now.
            finding = RiskService._calculate_feature_risk(
                feature_map["unique_contributors"],
                "CONTRIBUTOR_ACTIVITY",
                "Unusual spike in the number of unique contributors"
            )
            if finding: findings.append(finding)
            
        # Dependency Changes
        if "dependency_changes" in feature_map:
            finding = RiskService._calculate_feature_risk(
                feature_map["dependency_changes"],
                "DEPENDENCY_CHANGES",
                "High number of core dependency file modifications detected"
            )
            if finding: findings.append(finding)

        return findings

    @staticmethod
    def calculate_risk_score(findings: List[RiskFinding]) -> float:
        # Base scores if no anomalies
        category_scores = {
            "CODE_CHURN": 0.1,
            "CHANGE_SCOPE": 0.1,
            "COMMIT_ACTIVITY": 0.1,
            "PR_ACTIVITY": 0.1,
            "CONTRIBUTOR_ACTIVITY": 0.1
        }
        
        # Override with highest anomaly score per category
        for finding in findings:
            if finding.score > category_scores.get(finding.category, 0.0):
                category_scores[finding.category] = finding.score

        # Calculate weighted sum
        total_score = 0.0
        for category, weight in RiskService.WEIGHTS.items():
            total_score += category_scores.get(category, 0.0) * weight
            
        # Clamp between 0 and 1
        return min(max(total_score, 0.0), 1.0)

    @staticmethod
    def determine_risk_level(score: float) -> Severity:
        if score >= RiskService.RISK_LEVELS["HIGH"]:
            return Severity.HIGH
        if score >= RiskService.RISK_LEVELS["MEDIUM"]:
            return Severity.MEDIUM
        return Severity.LOW

    @staticmethod
    def calculate_confidence(baseline: BaselineAnalysis) -> float:
        """
        Confidence drops if there are fewer historical releases to compare against.
        """
        historical_count = baseline.historical_releases_count
        
        if historical_count == 0:
            return 0.1
        if historical_count < 3:
            return 0.4
        if historical_count < 5:
            return 0.6
        if historical_count < 10:
            return 0.8
            
        return 0.95 # High confidence with 10+ historical baselines

    @staticmethod
    def determine_trend(current_score: float, previous_scores: List[float]) -> RiskTrend:
        if not previous_scores:
            return RiskTrend.UNKNOWN
            
        # Compare current against the immediately preceding release
        previous = previous_scores[0]
        
        diff = current_score - previous
        
        if diff > 0.1:
            return RiskTrend.INCREASING
        elif diff < -0.1:
            return RiskTrend.DECREASING
        
        return RiskTrend.STABLE

    @staticmethod
    def evaluate_release(baseline: BaselineAnalysis, previous_risk_scores: List[float] = None) -> RiskAssessment:
        if previous_risk_scores is None:
            previous_risk_scores = []
            
        findings = RiskService.analyze_anomalies(baseline)
        score = round(RiskService.calculate_risk_score(findings), 2)
        level = RiskService.determine_risk_level(score)
        confidence = RiskService.calculate_confidence(baseline)
        trend = RiskService.determine_trend(score, previous_scores=previous_risk_scores)
        
        return RiskAssessment(
            repository=baseline.repository,
            release=baseline.target_release,
            risk_score=score,
            risk_level=level,
            confidence=confidence,
            trend=trend,
            findings=findings
        )
