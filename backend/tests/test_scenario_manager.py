"""
Unit tests for ScenarioManager.
Tests preset list, lookup, fallback.
STRICT RULE: No source file is modified.
"""
import pytest
from app.adapters.scenario_manager import ScenarioManager


REQUIRED_KEYS = {"id", "name", "description", "expected_risk"}


class TestScenarioManager:

    def test_get_all_scenarios_returns_5(self):
        scenarios = ScenarioManager.get_all_scenarios()
        assert len(scenarios) == 5

    def test_all_scenarios_have_required_keys(self):
        for s in ScenarioManager.get_all_scenarios():
            for key in REQUIRED_KEYS:
                assert key in s, f"Scenario {s.get('id')} missing key: {key}"

    def test_standard_healthy_expected_risk_low(self):
        s = ScenarioManager.get_scenario("standard_healthy")
        assert s["expected_risk"] == "LOW"

    def test_high_risk_hotfix_expected_risk_high(self):
        s = ScenarioManager.get_scenario("high_risk_hotfix")
        assert s["expected_risk"] == "HIGH"

    def test_test_regression_expected_risk_high(self):
        s = ScenarioManager.get_scenario("test_regression")
        assert s["expected_risk"] == "HIGH"

    def test_blocker_defects_expected_risk_critical(self):
        s = ScenarioManager.get_scenario("blocker_defects")
        assert s["expected_risk"] == "CRITICAL"

    def test_ops_instability_expected_risk_critical(self):
        s = ScenarioManager.get_scenario("ops_instability")
        assert s["expected_risk"] == "CRITICAL"

    def test_nonexistent_scenario_returns_first_preset(self):
        s = ScenarioManager.get_scenario("does_not_exist_xyz")
        assert s["id"] == "standard_healthy"

    def test_scenario_ids_are_unique(self):
        scenarios = ScenarioManager.get_all_scenarios()
        ids = [s["id"] for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_scenario_names_are_non_empty(self):
        for s in ScenarioManager.get_all_scenarios():
            assert s["name"].strip() != ""

    def test_scenario_descriptions_are_non_empty(self):
        for s in ScenarioManager.get_all_scenarios():
            assert s["description"].strip() != ""

    def test_expected_risk_values_are_valid(self):
        valid = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        for s in ScenarioManager.get_all_scenarios():
            assert s["expected_risk"] in valid

    def test_get_all_returns_list(self):
        result = ScenarioManager.get_all_scenarios()
        assert isinstance(result, list)

    def test_get_scenario_returns_dict(self):
        result = ScenarioManager.get_scenario("blocker_defects")
        assert isinstance(result, dict)
