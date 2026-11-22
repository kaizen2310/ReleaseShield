"""
Unit tests for XGBoostRiskModel (ML prediction pipeline).
Tests singleton pattern, score clamping, risk drivers, statistical fallback.
STRICT RULE: No source file is modified.
"""
import pytest
from unittest.mock import patch
from app.ml.risk_model import XGBoostRiskModel, FEATURE_NAMES, BASELINES


def _healthy_features():
    return {
        "code_churn": 800.0,
        "files_changed": 20.0,
        "avg_pr_merge_time_hours": 24.0,
        "high_risk_files": 1.0,
        "test_pass_rate_pct": 100.0,
        "coverage_delta_pct": 0.0,
        "flaky_tests_count": 0.0,
        "open_blockers": 0.0,
        "open_critical": 0.0,
        "defect_density": 0.3,
        "pipeline_success_rate_pct": 100.0,
        "staging_rollbacks": 0.0,
        "infra_config_drift": 0.0,
    }


def _critical_features():
    return {
        "code_churn": 15000.0,
        "files_changed": 200.0,
        "avg_pr_merge_time_hours": 1.5,
        "high_risk_files": 15.0,
        "test_pass_rate_pct": 82.0,
        "coverage_delta_pct": -12.0,
        "flaky_tests_count": 18.0,
        "open_blockers": 3.0,
        "open_critical": 7.0,
        "defect_density": 4.5,
        "pipeline_success_rate_pct": 65.0,
        "staging_rollbacks": 2.0,
        "infra_config_drift": 1.0,
    }


class TestXGBoostRiskModel:

    def test_singleton_pattern(self):
        """Two calls to XGBoostRiskModel() must return the same instance."""
        m1 = XGBoostRiskModel()
        m2 = XGBoostRiskModel()
        assert m1 is m2

    def test_predict_returns_tuple(self):
        model = XGBoostRiskModel()
        result = model.predict(_healthy_features())
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_predict_score_type_float(self):
        model = XGBoostRiskModel()
        score, _ = model.predict(_healthy_features())
        assert isinstance(score, float)

    def test_predict_score_clamped(self):
        model = XGBoostRiskModel()
        score, _ = model.predict(_healthy_features())
        assert 0.02 <= score <= 0.99

    def test_predict_drivers_is_list(self):
        model = XGBoostRiskModel()
        _, drivers = model.predict(_healthy_features())
        assert isinstance(drivers, list)

    def test_predict_drivers_max_6(self):
        model = XGBoostRiskModel()
        _, drivers = model.predict(_critical_features())
        assert len(drivers) <= 6

    def test_healthy_score_lower_than_critical(self):
        model = XGBoostRiskModel()
        healthy_score, _ = model.predict(_healthy_features())
        critical_score, _ = model.predict(_critical_features())
        assert healthy_score < critical_score

    def test_risk_drivers_sorted_descending(self):
        """Drivers should be sorted by contribution_pct descending."""
        model = XGBoostRiskModel()
        _, drivers = model.predict(_critical_features())
        for i in range(len(drivers) - 1):
            assert drivers[i].contribution_pct >= drivers[i + 1].contribution_pct

    def test_risk_driver_fields_present(self):
        model = XGBoostRiskModel()
        _, drivers = model.predict(_critical_features())
        if drivers:
            d = drivers[0]
            assert hasattr(d, "feature_name")
            assert hasattr(d, "display_name")
            assert hasattr(d, "importance_score")
            assert hasattr(d, "contribution_pct")
            assert hasattr(d, "impact_level")
            assert hasattr(d, "description")
            assert d.impact_level in ("HIGH", "MEDIUM", "LOW")

    def test_blocker_drives_critical_score(self):
        """3 open blockers should produce a significantly higher score than 0."""
        model = XGBoostRiskModel()
        no_blockers = {**_healthy_features(), "open_blockers": 0.0}
        with_blockers = {**_healthy_features(), "open_blockers": 3.0}
        s0, _ = model.predict(no_blockers)
        s1, _ = model.predict(with_blockers)
        assert s1 > s0

    def test_statistical_score_clamped(self):
        model = XGBoostRiskModel()
        stat_score = model._compute_statistical_score(_critical_features())
        assert 0.05 <= stat_score <= 0.95

    def test_statistical_score_healthy_low(self):
        model = XGBoostRiskModel()
        stat_score = model._compute_statistical_score(_healthy_features())
        assert stat_score < 0.30

    def test_statistical_score_critical_high(self):
        model = XGBoostRiskModel()
        stat_score = model._compute_statistical_score(_critical_features())
        assert stat_score > 0.50

    def test_feature_names_match_model(self):
        """FEATURE_NAMES should cover all expected features."""
        expected = {
            "code_churn", "files_changed", "avg_pr_merge_time_hours", "high_risk_files",
            "test_pass_rate_pct", "coverage_delta_pct", "flaky_tests_count",
            "open_blockers", "open_critical", "defect_density",
            "pipeline_success_rate_pct", "staging_rollbacks", "infra_config_drift"
        }
        assert set(FEATURE_NAMES) == expected

    def test_missing_features_default_to_zero(self):
        """Model must handle empty feature dict without raising."""
        model = XGBoostRiskModel()
        score, _ = model.predict({})
        assert 0.02 <= score <= 0.99
