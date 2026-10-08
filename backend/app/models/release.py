from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import UniqueConstraint
from app.db.database import Base

class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (UniqueConstraint('repository_id', 'tag_name', name='_repo_tag_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    tag_name = Column(String, index=True, nullable=False)
    previous_tag = Column(String, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    repository = relationship("Repository")
    metrics = relationship("GitMetricsDB", back_populates="release", uselist=False)
