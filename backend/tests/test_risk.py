import pytest
from app.services.risk_service import RiskService
from app.schemas.risk import BaselineAnalysis, BaselineStatistic, Severity, RiskTrend

def test_risk_scoring_and_severity():
    # Setup a baseline with severe anomalies
    baseline = BaselineAnalysis(
        repository="test/repo",
        target_release="v1",
        historical_releases_count=10,
        features=[
            BaselineStatistic(
                feature="code_churn",
                current=3000,
                historical_mean=1000,
                historical_median=900,
                minimum=500,
                maximum=1200,
                standard_deviation=200,
                ratio=3.0, # HIGH RATIO
                deviation_from_mean=2000,
                z_score=10.0
            )
        ]
    )
    
    findings = RiskService.analyze_anomalies(baseline)
    assert len(findings) == 1
    assert findings[0].category == "CODE_CHURN"
    assert findings[0].severity == Severity.HIGH
    
    score = RiskService.calculate_risk_score(findings)
    # 0.85 (High score) * 0.30 (Code Churn Weight) + 0.1 * other weights (4 * 0.1 * weights...)
    # Actually logic uses highest finding per category. Others default to 0.1 base score.
    # Base: Change (0.25*0.1=0.025) + Commit (0.20*0.1=0.02) + PR (0.15*0.1=0.015) + Contributor (0.10*0.1=0.01) = 0.07
    # Churn: 0.85 * 0.30 = 0.255
    # Total = 0.255 + 0.07 = 0.325 -> Rounds to 0.33 which is MEDIUM risk level
    assert score > 0.25
    assert score <= 1.0

def test_confidence_scaling():
    def get_conf(count):
        baseline = BaselineAnalysis(
            repository="test/repo",
            target_release="v1",
            historical_releases_count=count,
            features=[]
        )
        return RiskService.calculate_confidence(baseline)
        
    assert get_conf(0) == 0.1
    assert get_conf(2) == 0.4
    assert get_conf(4) == 0.6
    assert get_conf(9) == 0.8
    assert get_conf(12) == 0.95

def test_trend_calculation():
    assert RiskService.determine_trend(0.8, [0.4, 0.3]) == RiskTrend.INCREASING
    assert RiskService.determine_trend(0.2, [0.6, 0.7]) == RiskTrend.DECREASING
    assert RiskService.determine_trend(0.5, [0.55, 0.5]) == RiskTrend.STABLE
    assert RiskService.determine_trend(0.5, []) == RiskTrend.UNKNOWN
