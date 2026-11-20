from typing import Dict, Any, List, Tuple
from app.schemas.unified_risk import (
    Severity, AgentResult, HybridEngineBreakdown, RiskDriver, RiskTrend
)
from app.ml.risk_model import XGBoostRiskModel

class HybridRiskEngine:
    """
    Hybrid Release Risk Engine.
    Combines:
    1. Deterministic domain agent rule-evaluations (hard gates for safety & compliance)
    2. XGBoost machine learning model (probabilistic risk scoring & feature importance drivers)
    Ensures safety while providing deep statistical insight.
    """
    
    # Weight distribution across domain agents for the deterministic score
    DOMAIN_WEIGHTS = {
        "CODE": 0.25,
        "TEST": 0.25,
        "DEFECT": 0.30,
        "OPERATIONS": 0.20
    }
    
    @classmethod
    def evaluate(
        cls,
        code_result: AgentResult,
        test_result: AgentResult,
        defect_result: AgentResult,
        ops_result: AgentResult,
        previous_scores: List[float] = None
    ) -> Tuple[float, Severity, HybridEngineBreakdown, List[RiskDriver], RiskTrend]:
        
        # 1. Deterministic Rule Score
        det_score = (
            code_result.risk_score * cls.DOMAIN_WEIGHTS["CODE"] +
            test_result.risk_score * cls.DOMAIN_WEIGHTS["TEST"] +
            defect_result.risk_score * cls.DOMAIN_WEIGHTS["DEFECT"] +
            ops_result.risk_score * cls.DOMAIN_WEIGHTS["OPERATIONS"]
        )
        det_score = round(min(max(det_score, 0.05), 1.0), 2)
        
        # 2. Extract normalized feature vector for XGBoost Model
        c_m = code_result.metrics
        t_m = test_result.metrics
        d_m = defect_result.metrics
        o_m = ops_result.metrics
        
        features = {
            "code_churn": c_m.get("code_churn", 0),
            "files_changed": c_m.get("files_changed", 0),
            "avg_pr_merge_time_hours": c_m.get("avg_pr_merge_time_hours", 24.0),
            "high_risk_files": c_m.get("high_risk_files_touched", 0),
            "test_pass_rate_pct": t_m.get("pass_rate_pct", 100.0),
            "coverage_delta_pct": t_m.get("coverage_delta_pct", 0.0),
            "flaky_tests_count": t_m.get("flaky_tests_count", 0),
            "open_blockers": d_m.get("open_blockers", 0),
            "open_critical": d_m.get("open_critical", 0),
            "defect_density": d_m.get("defect_density_per_kloc", 0.0),
            "pipeline_success_rate_pct": o_m.get("pipeline_success_rate_pct", 100.0),
            "staging_rollbacks": o_m.get("staging_rollbacks_7d", 0),
            "infra_config_drift": 1.0 if o_m.get("infra_config_drift", False) else 0.0
        }
        
        # 3. Predict via XGBoost model and extract risk drivers
        model = XGBoostRiskModel()
        xgb_score, risk_drivers = model.predict(features)
        
        # 4. Blend scores (50% ML + 50% Deterministic Rules)
        blended = (0.50 * xgb_score) + (0.50 * det_score)
        
        # 5. HARD GATES (Safety Enforcements)
        hard_gate_triggered = False
        hard_gate_reason = None
        
        # Hard Gate A: Any open BLOCKER defects guarantee CRITICAL severity
        if d_m.get("open_blockers", 0) > 0:
            hard_gate_triggered = True
            hard_gate_reason = f"HARD GATE: {d_m.get('open_blockers')} open BLOCKER defect(s) strictly prevent release."
            blended = max(blended, 0.90)
            
        # Hard Gate B: Test pass rate below 92% guarantees HIGH/CRITICAL severity
        elif t_m.get("pass_rate_pct", 100.0) < 92.0:
            hard_gate_triggered = True
            hard_gate_reason = f"HARD GATE: Test pass rate ({t_m.get('pass_rate_pct')}%) is below minimum threshold (92%)."
            blended = max(blended, 0.80)
            
        # Hard Gate C: Multiple staging rollbacks
        elif o_m.get("staging_rollbacks_7d", 0) >= 2:
            hard_gate_triggered = True
            hard_gate_reason = "HARD GATE: 2+ staging deployment rollbacks in recent cycle."
            blended = max(blended, 0.85)
            
        final_score = round(min(max(blended, 0.02), 0.99), 2)
        
        # Determine Severity Level
        if final_score >= 0.80:
            level = Severity.CRITICAL
        elif final_score >= 0.60:
            level = Severity.HIGH
        elif final_score >= 0.30:
            level = Severity.MEDIUM
        else:
            level = Severity.LOW
            
        # Trend
        trend = RiskTrend.STABLE
        if previous_scores and len(previous_scores) > 0:
            prev = previous_scores[0]
            if final_score - prev > 0.08:
                trend = RiskTrend.INCREASING
            elif prev - final_score > 0.08:
                trend = RiskTrend.DECREASING
                
        breakdown = HybridEngineBreakdown(
            xgboost_risk_score=xgb_score,
            deterministic_rule_score=det_score,
            blended_risk_score=final_score,
            hard_gate_triggered=hard_gate_triggered,
            hard_gate_reason=hard_gate_reason,
            model_version="XGBoost v3.4 + Deterministic Multi-Agent Gates"
        )
        
        return final_score, level, breakdown, risk_drivers, trend
