from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db.database import Base

class ApprovalRecord(Base):
    __tablename__ = "release_approvals"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String, index=True, nullable=False)
    release = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default="PENDING_APPROVAL") # PENDING_APPROVAL, APPROVED, REJECTED, CHANGES_REQUESTED
    approver_name = Column(String, nullable=True)
    approver_role = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    actions_completed = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
