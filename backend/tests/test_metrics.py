import pytest
from app.services.metrics_service import MetricsService
from app.schemas.metrics import GitMetrics

def test_code_churn_calculation():
    release_data = {
        "target_release": {"published_at": "2024-05-14T18:00:00Z"},
        "previous_release": {"published_at": "2024-05-01T18:00:00Z"},
        "comparison": {
            "files": [
                {"additions": 100, "deletions": 40},
                {"additions": 50, "deletions": 10}
            ]
        }
    }
    
    metrics = MetricsService.calculate_metrics(release_data, pr_data=[])
    
    # 100 + 40 + 50 + 10 = 200
    assert metrics.code_churn == 200
    assert metrics.files_changed == 2
    assert metrics.lines_added == 150
    assert metrics.lines_deleted == 50
    assert metrics.avg_changes_per_file == 100.0

def test_commit_calculations():
    release_data = {
        "target_release": {"published_at": "2024-05-11T18:00:00Z"}, # 10 days
        "previous_release": {"published_at": "2024-05-01T18:00:00Z"},
        "comparison": {
            "commits": [
                {"author": {"login": "user1"}, "parents": [{}]},
                {"author": {"login": "user2"}, "parents": [{}]},
                {"author": {"login": "user1"}, "parents": [{}, {}]}, # Merge commit
            ]
        }
    }
    
    metrics = MetricsService.calculate_metrics(release_data, pr_data=[])
    
    assert metrics.release_interval_days == 10
    assert metrics.commit_count == 3
    assert metrics.merge_commit_count == 1
    assert metrics.unique_contributors == 2
    assert metrics.commits_per_day == 0.3
    assert metrics.commits_per_contributor == 1.5

def test_pr_merge_time_calculation():
    release_data = {
        "target_release": {"published_at": "2024-05-11T18:00:00Z"},
        "previous_release": {"published_at": "2024-05-01T18:00:00Z"},
        "comparison": {}
    }
    
    pr_data = [
        {"created_at": "2024-05-01T10:00:00Z", "merged_at": "2024-05-01T12:00:00Z", "additions": 10, "deletions": 5}, # 2 hours
        {"created_at": "2024-05-01T10:00:00Z", "merged_at": "2024-05-02T10:00:00Z", "additions": 800, "deletions": 300}, # 24 hours, Large PR (1100 churn)
        {"created_at": "2024-05-01T10:00:00Z", "merged_at": None}, # Closed but not merged
    ]
    
    metrics = MetricsService.calculate_metrics(release_data, pr_data)
    
    assert metrics.pr_count == 3
    assert metrics.merged_pr_count == 2
    assert metrics.avg_pr_merge_time_hours == 13.0 # (2 + 24) / 2
    assert metrics.max_pr_merge_time_hours == 24.0
    assert metrics.large_pr_count == 1 # 1100 > 1000 threshold
