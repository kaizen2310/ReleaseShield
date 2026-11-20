from datetime import datetime
from typing import Dict, Any, List, Optional
from app.db.database import SessionLocal
from app.models.approval import ApprovalRecord
from app.schemas.unified_risk import (
    ApprovalStatus, HumanApprovalDetails, ActionStatus
)

# In-memory store for fallback if DB is temporarily offline
_IN_MEMORY_APPROVALS: Dict[str, Dict[str, Any]] = {}

class ApprovalService:
    @staticmethod
    def _key(repository: str, release: str) -> str:
        return f"{repository.strip().lower()}::{release.strip().lower()}"

    @classmethod
    def get_approval(cls, repository: str, release: str) -> HumanApprovalDetails:
        key = cls._key(repository, release)
        
        # Check DB
        try:
            db = SessionLocal()
            rec = db.query(ApprovalRecord).filter(
                ApprovalRecord.repository == repository,
                ApprovalRecord.release == release
            ).order_by(ApprovalRecord.id.desc()).first()
            if rec:
                return HumanApprovalDetails(
                    status=ApprovalStatus(rec.status),
                    approver_name=rec.approver_name,
                    approver_role=rec.approver_role,
                    notes=rec.notes,
                    timestamp=rec.created_at.isoformat() if rec.created_at else None,
                    deployment_blocked=(rec.status != ApprovalStatus.APPROVED.value)
                )
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
                
        # Check in-memory fallback
        if key in _IN_MEMORY_APPROVALS:
            data = _IN_MEMORY_APPROVALS[key]
            return HumanApprovalDetails(
                status=ApprovalStatus(data["status"]),
                approver_name=data.get("approver_name"),
                approver_role=data.get("approver_role"),
                notes=data.get("notes"),
                timestamp=data.get("timestamp"),
                deployment_blocked=(data["status"] != ApprovalStatus.APPROVED.value)
            )
            
        return HumanApprovalDetails(
            status=ApprovalStatus.PENDING_APPROVAL,
            approver_name=None,
            approver_role=None,
            notes="Release is pending human review and sign-off.",
            timestamp=None,
            deployment_blocked=True
        )

    @classmethod
    def submit_approval(
        cls,
        repository: str,
        release: str,
        status: ApprovalStatus,
        approver_name: str,
        approver_role: str,
        notes: str
    ) -> HumanApprovalDetails:
        key = cls._key(repository, release)
        now_iso = datetime.utcnow().isoformat()
        
        # Save to memory fallback
        _IN_MEMORY_APPROVALS[key] = {
            "status": status.value,
            "approver_name": approver_name,
            "approver_role": approver_role,
            "notes": notes,
            "timestamp": now_iso
        }
        
        # Save to DB
        try:
            db = SessionLocal()
            rec = ApprovalRecord(
                repository=repository,
                release=release,
                status=status.value,
                approver_name=approver_name,
                approver_role=approver_role,
                notes=notes
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
        except Exception:
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass
                
        return HumanApprovalDetails(
            status=status,
            approver_name=approver_name,
            approver_role=approver_role,
            notes=notes,
            timestamp=now_iso,
            deployment_blocked=(status != ApprovalStatus.APPROVED)
        )
