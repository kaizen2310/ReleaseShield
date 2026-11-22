"""
Unit tests for BaselineService.
Tests statistics, z-scores, edge cases with empty/small history.
NOTE: BaselineService.calculate_statistics signature is:
  calculate_statistics(feature_name: str, current_value: float, historical_values: List[float]) -> BaselineStatistic
  Returns a BaselineStatistic Pydantic object with fields:
    feature, current, historical_mean, historical_median, minimum, maximum,
    standard_deviation, ratio, deviation_from_mean, z_score
STRICT RULE: No source file is modified.
"""
import pytest
from app.services.baseline_service import BaselineService


class TestBaselineServiceCalculateStatistics:

    def test_empty_history_ratio_999_if_current_positive(self):
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [])
        assert stat.ratio == 999.0

    def test_empty_history_z_score_0(self):
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [])
        assert stat.z_score == 0.0

    def test_empty_history_mean_is_zero(self):
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [])
        assert stat.historical_mean == 0.0

    def test_empty_history_current_zero_ratio_1(self):
        stat = BaselineService.calculate_statistics("code_churn", 0.0, [])
        assert stat.ratio == 1.0

    def test_one_value_less_than_min_observations_std_dev_0(self):
        """With < 3 historical values, std_dev should be 0."""
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [40.0])
        assert stat.standard_deviation == 0.0

    def test_two_values_less_than_min_observations_std_dev_0(self):
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [40.0, 45.0])
        assert stat.standard_deviation == 0.0

    def test_three_values_computes_mean(self):
        stat = BaselineService.calculate_statistics("code_churn", 45.0, [30.0, 40.0, 50.0])
        assert abs(stat.historical_mean - 40.0) < 0.01

    def test_three_values_computes_median(self):
        stat = BaselineService.calculate_statistics("code_churn", 25.0, [10.0, 20.0, 30.0])
        assert abs(stat.historical_median - 20.0) < 0.01

    def test_current_zero_mean_zero_ratio_1(self):
        stat = BaselineService.calculate_statistics("code_churn", 0.0, [0.0, 0.0, 0.0])
        assert stat.ratio == 1.0

    def test_current_positive_mean_zero_ratio_999(self):
        stat = BaselineService.calculate_statistics("code_churn", 10.0, [0.0, 0.0, 0.0])
        assert stat.ratio == 999.0

    def test_std_dev_zero_deviation_zero_z_score_0(self):
        """All historical same, current == mean → z_score 0."""
        stat = BaselineService.calculate_statistics("code_churn", 40.0, [40.0, 40.0, 40.0])
        assert stat.z_score == 0.0

    def test_std_dev_zero_positive_deviation_z_score_999(self):
        """All historical same, current > mean → z_score = 999."""
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [40.0, 40.0, 40.0])
        assert stat.z_score == 999.0

    def test_known_values_ratio(self):
        """Current=200, mean=100 → ratio=2.0."""
        stat = BaselineService.calculate_statistics("code_churn", 200.0, [100.0, 100.0, 100.0])
        assert abs(stat.ratio - 2.0) < 0.01

    def test_min_max_populated(self):
        stat = BaselineService.calculate_statistics("files_changed", 25.0, [10.0, 20.0, 30.0])
        assert stat.minimum == 10.0
        assert stat.maximum == 30.0

    def test_feature_name_stored(self):
        stat = BaselineService.calculate_statistics("my_feature", 10.0, [5.0, 10.0, 15.0])
        assert stat.feature == "my_feature"

    def test_std_dev_nonzero_with_3_obs(self):
        stat = BaselineService.calculate_statistics("code_churn", 50.0, [10.0, 20.0, 30.0])
        assert stat.standard_deviation > 0.0


class TestBaselineServiceAnalyzeBaseline:

    def _make_git_metrics(self):
        from app.schemas.metrics import GitMetrics
        return GitMetrics(
            release_interval_days=14,
            commit_count=5, files_changed=20, lines_added=500, lines_deleted=200,
            code_churn=700, unique_contributors=3, pr_count=4, merged_pr_count=4,
            avg_pr_merge_time_hours=12.0, max_pr_merge_time_hours=24.0, large_pr_count=0,
            dependency_changes=0, merge_commit_count=2,
            commits_per_day=1.5, commits_per_contributor=1.5, avg_changes_per_file=35.0
        )

    def test_analyze_baseline_returns_object(self):
        """analyze_baseline with no historical metrics should still return an object."""
        mock_metrics = self._make_git_metrics()
        result = BaselineService.analyze_baseline("owner", "my-repo", "v1.0.0", mock_metrics, [])
        assert result is not None
        assert result.repository == "owner/my-repo"

    def test_analyze_baseline_empty_history_features(self):
        mock_metrics = self._make_git_metrics()
        result = BaselineService.analyze_baseline("owner", "repo", "v2.0.0", mock_metrics, [])
        # With no historical, all ratios should be 999.0 or 1.0
        for stat in result.features:
            assert stat.ratio in (1.0, 999.0)
