from pydantic import BaseModel
from typing import Optional

class GitMetrics(BaseModel):
    # Release info
    release_interval_days: int

    # Commit info
    commit_count: int
    merge_commit_count: int
    unique_contributors: int
    commits_per_day: float
    commits_per_contributor: float

    # Code churn
    files_changed: int
    lines_added: int
    lines_deleted: int
    code_churn: int
    avg_changes_per_file: float
    dependency_changes: int

    # PR info
    pr_count: int
    merged_pr_count: int
    avg_pr_merge_time_hours: float
    max_pr_merge_time_hours: float
    large_pr_count: int
