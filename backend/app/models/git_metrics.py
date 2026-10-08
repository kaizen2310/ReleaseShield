from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class GitMetricsDB(Base):
    __tablename__ = "git_metrics"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Release info
    release_interval_days = Column(Integer, nullable=False)

    # Commit info
    commit_count = Column(Integer, nullable=False)
    merge_commit_count = Column(Integer, nullable=False)
    unique_contributors = Column(Integer, nullable=False)
    commits_per_day = Column(Float, nullable=False)
    commits_per_contributor = Column(Float, nullable=False)

    # Code churn
    files_changed = Column(Integer, nullable=False)
    lines_added = Column(Integer, nullable=False)
    lines_deleted = Column(Integer, nullable=False)
    code_churn = Column(Integer, nullable=False)
    avg_changes_per_file = Column(Float, nullable=False)
    dependency_changes = Column(Integer, nullable=False, default=0)

    # PR info
    pr_count = Column(Integer, nullable=False)
    merged_pr_count = Column(Integer, nullable=False)
    avg_pr_merge_time_hours = Column(Float, nullable=False)
    max_pr_merge_time_hours = Column(Float, nullable=False)
    large_pr_count = Column(Integer, nullable=False)

    release = relationship("Release", back_populates="metrics")
