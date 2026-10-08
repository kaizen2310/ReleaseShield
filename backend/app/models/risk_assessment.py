from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class RiskAssessmentDB(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    release_id = Column(Integer, ForeignKey("releases.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    release = relationship("Release")
    
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    trend = Column(String, nullable=False)
    
    findings_json = Column(JSON, nullable=True) # Storing findings as JSON for MVP simplicity
    llm_explanation = Column(String, nullable=True)
