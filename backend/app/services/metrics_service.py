from typing import Dict, Any, List
from datetime import datetime
from app.schemas.metrics import GitMetrics
from app.utils.dates import parse_github_date

class MetricsService:
    LARGE_PR_CHANGE_THRESHOLD = 1000

    @staticmethod
    def calculate_metrics(release_data: Dict[str, Any], pr_data: List[Dict[str, Any]] = None) -> GitMetrics:
        if pr_data is None:
            pr_data = []

        target = release_data["target_release"]
        previous = release_data["previous_release"]
        comparison = release_data["comparison"]

        # 1. Release Metrics
        target_date = parse_github_date(target.get("published_at") or target.get("created_at"))
        previous_date = parse_github_date(previous.get("published_at") or previous.get("created_at"))
        
        if target_date and previous_date:
            interval_days = (target_date - previous_date).days
            interval_days = max(1, interval_days)
        else:
            interval_days = 1

        # 2. Commit Metrics
        commits = comparison.get("commits", [])
        commit_count = len(commits)
        
        # Merge commits typically have >1 parents
        merge_commit_count = sum(1 for c in commits if len(c.get("parents", [])) > 1)
        
        unique_authors = set()
        for c in commits:
            author = c.get("author")
            if author:
                unique_authors.add(author.get("login", "unknown"))
            else:
                commit_author = c.get("commit", {}).get("author", {})
                unique_authors.add(commit_author.get("email", "unknown"))
                
        unique_contributors = len(unique_authors)
        commits_per_day = round(commit_count / interval_days, 2)
        commits_per_contributor = round(commit_count / max(1, unique_contributors), 2)

        # 3. Code Churn
        files = comparison.get("files", [])
        files_changed = len(files)
        
        lines_added = sum(f.get("additions", 0) for f in files)
        lines_deleted = sum(f.get("deletions", 0) for f in files)
        code_churn = lines_added + lines_deleted
        
        avg_changes_per_file = round(code_churn / max(1, files_changed), 2)
        
        dependency_files = ["package.json", "package-lock.json", "yarn.lock", "requirements.txt", "Pipfile", "Pipfile.lock", "pom.xml", "build.gradle", "go.mod", "go.sum", "Cargo.toml", "Cargo.lock"]
        dependency_changes = sum(1 for f in files if any(f.get("filename", "").endswith(df) for df in dependency_files))

        # 4. PR Metrics
        pr_count = len(pr_data)
        merged_prs = [pr for pr in pr_data if pr.get("merged_at")]
        merged_pr_count = len(merged_prs)
        
        merge_times = []
        large_prs = 0
        
        for pr in merged_prs:
            created_at = parse_github_date(pr["created_at"])
            merged_at = parse_github_date(pr["merged_at"])
            
            if created_at and merged_at:
                time_diff_hours = (merged_at - created_at).total_seconds() / 3600
                merge_times.append(time_diff_hours)
            
            pr_churn = pr.get("additions", 0) + pr.get("deletions", 0)
            if pr_churn >= MetricsService.LARGE_PR_CHANGE_THRESHOLD:
                large_prs += 1
                
        avg_pr_merge_time_hours = round(sum(merge_times) / max(1, len(merge_times)), 2)
        max_pr_merge_time_hours = round(max(merge_times) if merge_times else 0, 2)

        return GitMetrics(
            release_interval_days=interval_days,
            
            commit_count=commit_count,
            merge_commit_count=merge_commit_count,
            unique_contributors=unique_contributors,
            commits_per_day=commits_per_day,
            commits_per_contributor=commits_per_contributor,
            
            files_changed=files_changed,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            code_churn=code_churn,
            avg_changes_per_file=avg_changes_per_file,
            dependency_changes=dependency_changes,
            
            pr_count=pr_count,
            merged_pr_count=merged_pr_count,
            avg_pr_merge_time_hours=avg_pr_merge_time_hours,
            max_pr_merge_time_hours=max_pr_merge_time_hours,
            large_pr_count=large_prs
        )
