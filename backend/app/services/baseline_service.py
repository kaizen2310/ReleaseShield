import statistics
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.repository import Repository
from app.models.release import Release
from app.models.git_metrics import GitMetricsDB
from app.schemas.metrics import GitMetrics
from app.schemas.risk import BaselineStatistic, BaselineAnalysis

class BaselineService:
    # Minimum observations to calculate meaningful standard deviation
    MIN_OBSERVATIONS = 3
    
    # Features to track for risk analysis
    NUMERICAL_FEATURES = [
        "code_churn",
        "files_changed",
        "commits_per_day",
        "commits_per_contributor",
        "avg_changes_per_file",
        "avg_pr_merge_time_hours",
        "unique_contributors",
        "dependency_changes"
    ]

    @staticmethod
    def get_historical_metrics(db: Session, owner: str, repo_name: str, limit: int = 10) -> List[GitMetricsDB]:
        repo = db.query(Repository).filter(Repository.owner == owner, Repository.name == repo_name).first()
        if not repo:
            return []
            
        releases = (
            db.query(Release)
            .filter(Release.repository_id == repo.id)
            .order_by(Release.published_at.desc())
            .limit(limit)
            .all()
        )
        
        # We need the metrics connected to these releases
        metrics = []
        for r in releases:
            if r.metrics:
                metrics.append(r.metrics)
                
        return metrics

    @staticmethod
    def calculate_statistics(feature_name: str, current_value: float, historical_values: List[float]) -> BaselineStatistic:
        if not historical_values:
            return BaselineStatistic(
                feature=feature_name,
                current=current_value,
                historical_mean=0.0,
                historical_median=0.0,
                minimum=0.0,
                maximum=0.0,
                standard_deviation=0.0,
                ratio=1.0 if current_value == 0 else 999.0,
                deviation_from_mean=current_value,
                z_score=0.0
            )
            
        mean = statistics.mean(historical_values)
        median = statistics.median(historical_values)
        minimum = min(historical_values)
        maximum = max(historical_values)
        
        # Only calculate std_dev if we have enough observations, otherwise return 0.0 to avoid misleading confidence
        if len(historical_values) >= BaselineService.MIN_OBSERVATIONS:
            std_dev = statistics.stdev(historical_values)
        else:
            std_dev = 0.0
            
        # Fix division by zero
        if mean > 0:
            ratio = current_value / mean
        else:
            ratio = 1.0 if current_value == 0 else 999.0
            
        deviation = current_value - mean
        z_score = deviation / std_dev if std_dev > 0 else (0.0 if deviation == 0 else 999.0)
        
        return BaselineStatistic(
            feature=feature_name,
            current=float(current_value),
            historical_mean=float(mean),
            historical_median=float(median),
            minimum=float(minimum),
            maximum=float(maximum),
            standard_deviation=float(std_dev),
            ratio=float(ratio),
            deviation_from_mean=float(deviation),
            z_score=float(z_score)
        )

    @staticmethod
    def analyze_baseline(
        owner: str, 
        repo_name: str, 
        target_tag: str, 
        current_metrics: GitMetrics, 
        historical_metrics: List[GitMetricsDB]
    ) -> BaselineAnalysis:
        
        # Extract the historical values as dictionaries for easy querying
        historical_data = {
            feature: [getattr(m, feature) for m in historical_metrics if getattr(m, feature) is not None]
            for feature in BaselineService.NUMERICAL_FEATURES
        }
        
        stats = []
        for feature in BaselineService.NUMERICAL_FEATURES:
            current_val = getattr(current_metrics, feature)
            hist_vals = historical_data.get(feature, [])
            
            stat = BaselineService.calculate_statistics(feature, current_val, hist_vals)
            stats.append(stat)
            
        return BaselineAnalysis(
            repository=f"{owner}/{repo_name}",
            target_release=target_tag,
            historical_releases_count=len(historical_metrics),
            features=stats
        )
