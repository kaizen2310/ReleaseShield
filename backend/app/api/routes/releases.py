from fastapi import APIRouter, HTTPException, Query
from typing import Any, List, Dict
from app.schemas.unified_risk import (
    ReleaseAnalysisRequest, ApprovalSubmissionRequest,
    ActionToggleRequest, HumanApprovalDetails
)
from app.adapters.scenario_manager import ScenarioManager
from app.agents.multi_agent_orchestrator import create_multi_agent_orchestrator
from app.services.approval_service import ApprovalService

router = APIRouter()

# Initialize orchestrator graph once
multi_agent_orchestrator = create_multi_agent_orchestrator()

# In-memory tracking for action toggles (fallback)
_ACTION_TOGGLE_STORE: Dict[str, str] = {}

@router.post("/analyze")
async def analyze_release(request: ReleaseAnalysisRequest) -> Any:
    """
    Triggers the 4-Agent Orchestrator (Code, Test, Defect, Operations)
    and Hybrid Risk Engine (Deterministic Rules + XGBoost Model)
    to generate a complete, explainable release risk assessment.
    """
    if "/" not in request.repository:
        raise HTTPException(status_code=400, detail="Invalid repository format. Must be owner/name (e.g. facebook/react).")
    if not request.release:
        raise HTTPException(status_code=400, detail="Target release tag must be provided.")
        
    try:
        final_state = await multi_agent_orchestrator.ainvoke({"request": request.model_dump()})
        report = final_state.get("final_report", {})
        
        # Overlay any previously toggled action statuses
        for act in report.get("required_actions", []):
            toggle_key = f"{request.repository}::{request.release}::{act['id']}"
            if toggle_key in _ACTION_TOGGLE_STORE:
                act["status"] = _ACTION_TOGGLE_STORE[toggle_key]
                
        # Also provide backward-compatible flat fields for any legacy consumer
        report["metrics"] = report.get("code_agent", {}).get("metrics", {})
        report["findings"] = (
            report.get("code_agent", {}).get("findings", []) +
            report.get("test_agent", {}).get("findings", []) +
            report.get("defect_agent", {}).get("findings", []) +
            report.get("operations_agent", {}).get("findings", [])
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis orchestration failed: {str(e)}")

@router.get("/scenarios")
async def get_scenarios() -> List[Dict[str, Any]]:
    """Returns available release scenario presets for demonstration and testing."""
    return ScenarioManager.get_all_scenarios()

@router.post("/approval")
async def submit_approval(request: ApprovalSubmissionRequest) -> HumanApprovalDetails:
    """
    Submits a mandatory human approval decision (APPROVE, REJECT, CHANGES_REQUESTED).
    ReleaseShield provides release-readiness advisory; human sign-off is mandatory before deployment.
    """
    return ApprovalService.submit_approval(
        repository=request.repository,
        release=request.release,
        status=request.status,
        approver_name=request.approver_name,
        approver_role=request.approver_role,
        notes=request.notes or ""
    )

@router.get("/approval")
async def get_approval(
    repository: str = Query(..., description="Repository in owner/name format"),
    release: str = Query(..., description="Target release tag")
) -> HumanApprovalDetails:
    """Retrieves current human sign-off status for a given release."""
    return ApprovalService.get_approval(repository, release)

@router.post("/actions/toggle")
async def toggle_action(request: ActionToggleRequest) -> Dict[str, Any]:
    """Toggles status of an action in the release readiness checklist."""
    toggle_key = f"{request.repository}::{request.release}::{request.action_id}"
    _ACTION_TOGGLE_STORE[toggle_key] = request.status.value
    return {
        "action_id": request.action_id,
        "status": request.status.value,
        "waiver_reason": request.waiver_reason
    }
