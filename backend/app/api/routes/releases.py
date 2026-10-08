from fastapi import APIRouter, HTTPException, Depends
from typing import Any
from app.schemas.release import ReleaseRequest
from app.agents.git_agent.workflow import create_git_agent_workflow
from app.agents.git_agent.state import GitAgentState

router = APIRouter()

# Initialize the agent once to avoid recompiling on every request
git_agent = create_git_agent_workflow()

@router.post("/analyze")
async def analyze_release(request: ReleaseRequest) -> Any:
    """
    Triggers the LangGraph Git Agent to fully analyze a target release against its historical baseline.
    """
    initial_state = GitAgentState(
        repository=request.repository,
        target_release=request.release,
        historical_window=request.historical_window
    )
    
    # Run the agent asynchronously
    final_state = await git_agent.ainvoke(initial_state)
    
    if "error" in final_state and final_state["error"]:
        raise HTTPException(status_code=400, detail=final_state["error"])
        
    return {
        "repository": final_state.get("repository"),
        "release": final_state.get("target_release"),
        
        "risk_score": final_state.get("risk_score"),
        "risk_level": final_state.get("risk_level", "").value if hasattr(final_state.get("risk_level"), "value") else final_state.get("risk_level"),
        
        "confidence": final_state.get("confidence"),
        "trend": final_state.get("trend", "").value if hasattr(final_state.get("trend"), "value") else final_state.get("trend"),
        
        "summary": "Release analysis completed successfully.",
        
        "metrics": final_state.get("current_metrics", {}).model_dump() if final_state.get("current_metrics") else {},
        
        "findings": [f.model_dump() for f in final_state.get("findings", [])],
        "recommendations": final_state.get("recommendations", []),
        "explanation": final_state.get("llm_explanation", "")
    }

# Stub endpoints for future implementation
@router.get("/{owner}/{repo}/{release}")
async def get_release(owner: str, repo: str, release: str):
    return {"message": "Not implemented yet"}

@router.get("/{owner}/{repo}/{release}/metrics")
async def get_release_metrics(owner: str, repo: str, release: str):
    return {"message": "Not implemented yet"}

@router.get("/{owner}/{repo}/{release}/risk")
async def get_release_risk(owner: str, repo: str, release: str):
    return {"message": "Not implemented yet"}
