import os
import json
import logging
import numpy as np
import xgboost as xgb
from typing import Dict, Any, List, Tuple
from app.schemas.unified_risk import RiskDriver

logger = logging.getLogger(__name__)

FEATURE_METADATA = [
    {"name": "code_churn", "display": "Code Churn", "unit": "lines", "category": "CODE"},
    {"name": "files_changed", "display": "Files Modified", "unit": "files", "category": "CODE"},
    {"name": "avg_pr_merge_time_hours", "display": "PR Merge Velocity", "unit": "hrs", "category": "CODE"},
    {"name": "high_risk_files", "display": "Core / Config Touches", "unit": "files", "category": "CODE"},
    {"name": "test_pass_rate_pct", "display": "Test Pass Rate", "unit": "%", "category": "TEST"},
    {"name": "coverage_delta_pct", "display": "Coverage Delta", "unit": "%", "category": "TEST"},
    {"name": "flaky_tests_count", "display": "Flaky Tests", "unit": "tests", "category": "TEST"},
    {"name": "open_blockers", "display": "P0 Blocker Defects", "unit": "bugs", "category": "DEFECT"},
    {"name": "open_critical", "display": "P1 Critical Defects", "unit": "bugs", "category": "DEFECT"},
    {"name": "defect_density", "display": "Defect Density", "unit": "per KLOC", "category": "DEFECT"},
    {"name": "pipeline_success_rate_pct", "display": "CI/CD Pipeline Success", "unit": "%", "category": "OPERATIONS"},
    {"name": "staging_rollbacks", "display": "Staging Rollbacks (7d)", "unit": "rollbacks", "category": "OPERATIONS"},
    {"name": "infra_config_drift", "display": "Infrastructure Drift", "unit": "flag", "category": "OPERATIONS"},
]

FEATURE_NAMES = [f["name"] for f in FEATURE_METADATA]

class XGBoostRiskModel:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(XGBoostRiskModel, cls).__new__(cls)
            cls._instance._model = None
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        """Train or load the pre-trained XGBoost model on synthetic release telemetry."""
        logger.info("Initializing XGBoost release risk model...")
        X, y = self._generate_synthetic_training_data(n_samples=1200)
        
        self._model = xgb.XGBRegressor(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42
        )
        self._model.fit(X, y)
        logger.info("XGBoost release risk model trained successfully.")

    def _generate_synthetic_training_data(self, n_samples: int = 1200) -> Tuple[np.ndarray, np.ndarray]:
        np.random.seed(42)
        X = []
        y = []
        
        for _ in range(n_samples):
            # Sample release profile
            profile_type = np.random.choice(["healthy", "moderate", "high_risk", "critical"], p=[0.40, 0.30, 0.18, 0.12])
            
            if profile_type == "healthy":
                code_churn = np.random.uniform(200, 3000)
                files_changed = np.random.uniform(5, 40)
                avg_pr_merge = np.random.uniform(12, 48)
                high_risk_files = np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1])
                test_pass_rate = np.random.uniform(99.0, 100.0)
                coverage_delta = np.random.uniform(-1.0, 3.0)
                flaky_tests = np.random.choice([0, 1], p=[0.85, 0.15])
                open_blockers = 0
                open_critical = np.random.choice([0, 1], p=[0.8, 0.2])
                defect_density = np.random.uniform(0.1, 0.8)
                pipeline_success = np.random.uniform(96.0, 100.0)
                staging_rollbacks = 0
                infra_drift = 0
                risk_target = np.random.uniform(0.05, 0.25)
                
            elif profile_type == "moderate":
                code_churn = np.random.uniform(2500, 6000)
                files_changed = np.random.uniform(35, 75)
                avg_pr_merge = np.random.uniform(6, 30)
                high_risk_files = np.random.choice([1, 2, 4])
                test_pass_rate = np.random.uniform(96.0, 99.0)
                coverage_delta = np.random.uniform(-4.0, 0.5)
                flaky_tests = np.random.randint(1, 4)
                open_blockers = 0
                open_critical = np.random.choice([1, 2])
                defect_density = np.random.uniform(0.8, 1.8)
                pipeline_success = np.random.uniform(90.0, 96.0)
                staging_rollbacks = np.random.choice([0, 1], p=[0.85, 0.15])
                infra_drift = np.random.choice([0, 1], p=[0.75, 0.25])
                risk_target = np.random.uniform(0.35, 0.55)
                
            elif profile_type == "high_risk":
                code_churn = np.random.uniform(5500, 12000)
                files_changed = np.random.uniform(70, 140)
                avg_pr_merge = np.random.uniform(2, 10) # rushed
                high_risk_files = np.random.choice([4, 7, 10])
                test_pass_rate = np.random.uniform(92.0, 96.0)
                coverage_delta = np.random.uniform(-9.0, -3.0)
                flaky_tests = np.random.randint(4, 9)
                open_blockers = np.random.choice([0, 1], p=[0.4, 0.6])
                open_critical = np.random.randint(2, 5)
                defect_density = np.random.uniform(1.8, 3.2)
                pipeline_success = np.random.uniform(80.0, 90.0)
                staging_rollbacks = np.random.choice([0, 1, 2], p=[0.5, 0.35, 0.15])
                infra_drift = np.random.choice([0, 1], p=[0.4, 0.6])
                risk_target = np.random.uniform(0.65, 0.82)
                
            else: # critical
                code_churn = np.random.uniform(8000, 20000)
                files_changed = np.random.uniform(100, 250)
                avg_pr_merge = np.random.uniform(1, 6)
                high_risk_files = np.random.randint(8, 18)
                test_pass_rate = np.random.uniform(82.0, 92.0)
                coverage_delta = np.random.uniform(-15.0, -6.0)
                flaky_tests = np.random.randint(8, 20)
                open_blockers = np.random.randint(1, 4)
                open_critical = np.random.randint(3, 8)
                defect_density = np.random.uniform(2.5, 5.0)
                pipeline_success = np.random.uniform(60.0, 80.0)
                staging_rollbacks = np.random.randint(1, 3)
                infra_drift = 1
                risk_target = np.random.uniform(0.85, 0.98)
                
            sample = [
                code_churn, files_changed, avg_pr_merge, high_risk_files,
                test_pass_rate, coverage_delta, flaky_tests,
                open_blockers, open_critical, defect_density,
                pipeline_success, staging_rollbacks, infra_drift
            ]
            X.append(sample)
            y.append(risk_target)
            
        return np.array(X), np.array(y)

    def predict(self, feature_dict: Dict[str, Any]) -> Tuple[float, List[RiskDriver]]:
        """
        Runs XGBoost inference on the release feature vector and calculates
        feature-level contributions (Risk Drivers).
        """
        sample_vector = [float(feature_dict.get(name, 0.0)) for name in FEATURE_NAMES]
        X_sample = np.array([sample_vector])
        
        # Predict risk score
        raw_pred = float(self._model.predict(X_sample)[0])
        pred_score = min(max(raw_pred, 0.02), 0.99)
        
        # Calculate feature importances and contributions
        feature_importances = self._model.feature_importances_
        
        # Normalized anomaly weights relative to standard baseline expectations
        baselines = {
            "code_churn": 1500.0,
            "files_changed": 25.0,
            "avg_pr_merge_time_hours": 24.0,
            "high_risk_files": 1.0,
            "test_pass_rate_pct": 100.0,
            "coverage_delta_pct": 0.0,
            "flaky_tests_count": 0.0,
            "open_blockers": 0.0,
            "open_critical": 0.0,
            "defect_density": 0.5,
            "pipeline_success_rate_pct": 100.0,
            "staging_rollbacks": 0.0,
            "infra_config_drift": 0.0
        }
        
        raw_contributions = []
        for i, meta in enumerate(FEATURE_METADATA):
            feat_name = meta["name"]
            val = sample_vector[i]
            base = baselines.get(feat_name, 0.0)
            imp = float(feature_importances[i])
            
            # Anomaly severity calculation
            dev = 0.0
            if feat_name in ["test_pass_rate_pct", "pipeline_success_rate_pct"]:
                dev = max(0.0, (100.0 - val) / 10.0)
            elif feat_name == "coverage_delta_pct":
                dev = max(0.0, -val / 3.0)
            elif feat_name == "avg_pr_merge_time_hours":
                dev = max(0.0, (12.0 - val) / 4.0) if val < 12.0 else 0.0
            elif feat_name == "open_blockers":
                dev = val * 5.0 # Blocker bugs carry huge risk weight
            elif feat_name == "staging_rollbacks":
                dev = val * 4.0
            else:
                dev = max(0.0, (val - base) / max(base, 1.0))
                
            contribution = imp * dev
            raw_contributions.append((meta, val, base, imp, contribution))
            
        total_contrib = sum(c[4] for c in raw_contributions)
        if total_contrib <= 0:
            total_contrib = 1.0
            
        # Build structured RiskDriver objects sorted by highest contribution
        drivers: List[RiskDriver] = []
        for meta, val, base, imp, cont in raw_contributions:
            pct = round((cont / total_contrib) * 100.0, 1)
            if pct < 3.0 and val <= base:
                continue # Omit non-contributors
                
            impact_level = "HIGH" if pct >= 20.0 else ("MEDIUM" if pct >= 8.0 else "LOW")
            
            # Formulate concise human-readable explanation
            if meta["name"] == "open_blockers" and val > 0:
                desc = f"{int(val)} unresolved P0 Blocker defect(s) pending resolution."
            elif meta["name"] == "coverage_delta_pct" and val < 0:
                desc = f"{abs(val):.1f}% regression in automated test coverage."
            elif meta["name"] == "code_churn" and val > base:
                desc = f"{int(val):,} lines modified ({val/base:.1f}x historical baseline)."
            elif meta["name"] == "staging_rollbacks" and val > 0:
                desc = f"{int(val)} recent staging deployment rollback(s)."
            elif meta["name"] == "pipeline_success_rate_pct" and val < 95.0:
                desc = f"Pipeline stability degraded to {val:.1f}% success rate."
            elif meta["name"] == "test_pass_rate_pct" and val < 100.0:
                desc = f"Automated test pass rate at {val:.1f}%."
            elif meta["name"] == "infra_config_drift" and val > 0:
                desc = "Infrastructure/Environment configuration drift detected."
            else:
                desc = f"{meta['display']} current value {val:.1f} vs baseline {base:.1f}."
                
            drivers.append(RiskDriver(
                feature_name=meta["name"],
                display_name=meta["display"],
                importance_score=round(imp, 3),
                current_value=val,
                baseline_value=base,
                contribution_pct=pct,
                impact_level=impact_level,
                description=desc
            ))
            
        # Sort by contribution descending
        drivers.sort(key=lambda d: d.contribution_pct, reverse=True)
        return round(pred_score, 2), drivers[:6] # Return top 6 drivers
