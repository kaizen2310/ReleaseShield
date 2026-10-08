from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from app.models.repository import Repository
from app.models.release import Release
from app.models.git_metrics import GitMetricsDB
from app.models.risk_assessment import RiskAssessmentDB
from app.schemas.metrics import GitMetrics
import datetime

class PersistenceService:
    @staticmethod
    def get_or_create_repository(db: Session, owner: str, name: str) -> Repository:
        repo = db.query(Repository).filter(Repository.owner == owner, Repository.name == name).first()
        if not repo:
            repo = Repository(owner=owner, name=name)
            db.add(repo)
            db.commit()
            db.refresh(repo)
        return repo

    @staticmethod
    def get_or_create_release(db: Session, repository_id: int, tag_name: str, previous_tag: str = None, published_at: datetime.datetime = None) -> Release:
        release = db.query(Release).filter(Release.repository_id == repository_id, Release.tag_name == tag_name).first()
        if not release:
            release = Release(
                repository_id=repository_id,
                tag_name=tag_name,
                previous_tag=previous_tag,
                published_at=published_at
            )
            db.add(release)
            db.commit()
            db.refresh(release)
        else:
            # Update fields if provided
            modified = False
            if previous_tag and not release.previous_tag:
                release.previous_tag = previous_tag
                modified = True
            if published_at and not release.published_at:
                release.published_at = published_at
                modified = True
            if modified:
                db.commit()
                db.refresh(release)
                
        return release

    @staticmethod
    def persist_metrics(db: Session, release_id: int, metrics: GitMetrics) -> GitMetricsDB:
        db_metrics = db.query(GitMetricsDB).filter(GitMetricsDB.release_id == release_id).first()
        if not db_metrics:
            db_metrics = GitMetricsDB(
                release_id=release_id,
                release_interval_days=metrics.release_interval_days,
                commit_count=metrics.commit_count,
                merge_commit_count=metrics.merge_commit_count,
                unique_contributors=metrics.unique_contributors,
                commits_per_day=metrics.commits_per_day,
                commits_per_contributor=metrics.commits_per_contributor,
                files_changed=metrics.files_changed,
                lines_added=metrics.lines_added,
                lines_deleted=metrics.lines_deleted,
                code_churn=metrics.code_churn,
                avg_changes_per_file=metrics.avg_changes_per_file,
                pr_count=metrics.pr_count,
                merged_pr_count=metrics.merged_pr_count,
                avg_pr_merge_time_hours=metrics.avg_pr_merge_time_hours,
                max_pr_merge_time_hours=metrics.max_pr_merge_time_hours,
                large_pr_count=metrics.large_pr_count,
                dependency_changes=metrics.dependency_changes
            )
            db.add(db_metrics)
        else:
            db_metrics.release_interval_days = metrics.release_interval_days
            db_metrics.commit_count = metrics.commit_count
            db_metrics.merge_commit_count = metrics.merge_commit_count
            db_metrics.unique_contributors = metrics.unique_contributors
            db_metrics.commits_per_day = metrics.commits_per_day
            db_metrics.commits_per_contributor = metrics.commits_per_contributor
            db_metrics.files_changed = metrics.files_changed
            db_metrics.lines_added = metrics.lines_added
            db_metrics.lines_deleted = metrics.lines_deleted
            db_metrics.code_churn = metrics.code_churn
            db_metrics.avg_changes_per_file = metrics.avg_changes_per_file
            db_metrics.pr_count = metrics.pr_count
            db_metrics.merged_pr_count = metrics.merged_pr_count
            db_metrics.avg_pr_merge_time_hours = metrics.avg_pr_merge_time_hours
            db_metrics.max_pr_merge_time_hours = metrics.max_pr_merge_time_hours
            db_metrics.large_pr_count = metrics.large_pr_count
            db_metrics.dependency_changes = metrics.dependency_changes

        db.commit()
        db.refresh(db_metrics)
        return db_metrics

    @staticmethod
    def persist_risk_assessment(db: Session, release_id: int, risk_score: float, risk_level: str, confidence: float, trend: str, findings: list, llm_explanation: str = None) -> RiskAssessmentDB:
        assessment = db.query(RiskAssessmentDB).filter(RiskAssessmentDB.release_id == release_id).first()
        findings_dict = [f.model_dump() if hasattr(f, 'model_dump') else f for f in findings]
        
        if not assessment:
            assessment = RiskAssessmentDB(
                release_id=release_id,
                risk_score=risk_score,
                risk_level=risk_level,
                confidence=confidence,
                trend=trend,
                findings_json=findings_dict,
                llm_explanation=llm_explanation
            )
            db.add(assessment)
        else:
            assessment.risk_score = risk_score
            assessment.risk_level = risk_level
            assessment.confidence = confidence
            assessment.trend = trend
            assessment.findings_json = findings_dict
            if llm_explanation:
                assessment.llm_explanation = llm_explanation
                
        db.commit()
        db.refresh(assessment)
        return assessment
