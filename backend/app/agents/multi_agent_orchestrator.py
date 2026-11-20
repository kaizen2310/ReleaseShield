import json
import logging
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, END

from app.schemas.unified_risk import (
    ReleaseAnalysisRequest, UnifiedRiskReport, AgentResult,
    Severity, RiskTrend, HybridEngineBreakdown, RiskDriver,
    RequiredAction, HumanApprovalDetails, ReleaseType
)
from app.adapters.git_adapter import GitAdapter
from app.adapters.test_adapter import TestAdapter
from app.adapters.defect_adapter import DefectAdapter
from app.adapters.ops_adapter import OperationsAdapter
from app.agents.code_agent import CodeAgent
from app.agents.test_agent import TestAgent
from app.agents.defect_agent import DefectAgent
from app.agents.operations_agent import OperationsAgent
from app.services.hybrid_risk_engine import HybridRiskEngine
from app.services.recommendation_engine import RecommendationEngine
from app.services.approval_service import ApprovalService
from app.llm.explanation_service import LLMExplanationService

logger = logging.getLogger(__name__)

class MultiAgentState(TypedDict, total=False):
    request: Dict[str, Any]
    
    # Raw Adapter telemetry
    git_data: Dict[str, Any]
    test_data: Dict[str, Any]
    defect_data: Dict[str, Any]
    ops_data: Dict[str, Any]
    
    # Agent Results
    code_result: Dict[str, Any]
    test_result: Dict[str, Any]
    defect_result: Dict[str, Any]
    ops_result: Dict[str, Any]
    
    # Hybrid Engine Results
    risk_score: float
    risk_level: str
    hybrid_engine: Dict[str, Any]
    risk_drivers: List[Dict[str, Any]]
    trend: str
    confidence: float
    
    # Actions & Narrative
    recommendations: List[str]
    required_actions: List[Dict[str, Any]]
    explanation: str
    approval: Dict[str, Any]
    
    final_report: Dict[str, Any]
    error: str

# -------------------------------------------------------------
# Node Implementations
# -------------------------------------------------------------

async def gather_adapter_data_node(state: MultiAgentState) -> MultiAgentState:
    req = state["request"]
    repo = req.get("repository", "")
    release = req.get("release", "")
    
    context = {
        "scenario": req.get("scenario", "standard_healthy"),
        "release_type": req.get("release_type", "MINOR"),
        "custom_test_metrics": req.get("custom_test_metrics"),
        "custom_defect_metrics": req.get("custom_defect_metrics"),
        "custom_operations_metrics": req.get("custom_operations_metrics")
    }
    
    git_adapter = GitAdapter()
    test_adapter = TestAdapter()
    defect_adapter = DefectAdapter()
    ops_adapter = OperationsAdapter()
    
    git_data = await git_adapter.fetch_data(repo, release, context)
    test_data = await test_adapter.fetch_data(repo, release, context)
    defect_data = await defect_adapter.fetch_data(repo, release, context)
    ops_data = await ops_adapter.fetch_data(repo, release, context)
    
    return {
        "git_data": git_data,
        "test_data": test_data,
        "defect_data": defect_data,
        "ops_data": ops_data
    }

async def run_domain_agents_node(state: MultiAgentState) -> MultiAgentState:
    git_metrics = state["git_data"].get("metrics", {})
    test_metrics = state["test_data"]
    defect_metrics = state["defect_data"]
    ops_metrics = state["ops_data"]
    
    code_res = CodeAgent.evaluate(git_metrics)
    test_res = TestAgent.evaluate(test_metrics)
    defect_res = DefectAgent.evaluate(defect_metrics)
    ops_res = OperationsAgent.evaluate(ops_metrics)
    
    return {
        "code_result": code_res.model_dump(),
        "test_result": test_res.model_dump(),
        "defect_result": defect_res.model_dump(),
        "ops_result": ops_res.model_dump()
    }

async def run_hybrid_risk_engine_node(state: MultiAgentState) -> MultiAgentState:
    code_res = AgentResult(**state["code_result"])
    test_res = AgentResult(**state["test_result"])
    defect_res = AgentResult(**state["defect_result"])
    ops_res = AgentResult(**state["ops_result"])
    
    score, level, breakdown, drivers, trend = HybridRiskEngine.evaluate(
        code_result=code_res,
        test_result=test_res,
        defect_result=defect_res,
        ops_result=ops_res
    )
    
    return {
        "risk_score": score,
        "risk_level": level.value,
        "hybrid_engine": breakdown.model_dump(),
        "risk_drivers": [d.model_dump() for d in drivers],
        "trend": trend.value,
        "confidence": 0.94
    }

async def generate_recommendations_node(state: MultiAgentState) -> MultiAgentState:
    code_res = AgentResult(**state["code_result"])
    test_res = AgentResult(**state["test_result"])
    defect_res = AgentResult(**state["defect_result"])
    ops_res = AgentResult(**state["ops_result"])
    risk_level = state["risk_level"]
    
    recommendations, actions = RecommendationEngine.generate(
        code_result=code_res,
        test_result=test_res,
        defect_result=defect_res,
        ops_result=ops_res,
        risk_level=risk_level
    )
    
    return {
        "recommendations": recommendations,
        "required_actions": [a.model_dump() for a in actions]
    }

async def generate_explanation_node(state: MultiAgentState) -> MultiAgentState:
    req = state["request"]
    evidence = {
        "repository": req.get("repository"),
        "release": req.get("release"),
        "risk_score": state["risk_score"],
        "risk_level": state["risk_level"],
        "trend": state["trend"],
        "confidence": state["confidence"],
        "hybrid_engine": state["hybrid_engine"],
        "risk_drivers": state["risk_drivers"],
        "findings": (
            state["code_result"]["findings"] +
            state["test_result"]["findings"] +
            state["defect_result"]["findings"] +
            state["ops_result"]["findings"]
        ),
        "recommendations": state["recommendations"]
    }
    
    explanation = ""
    try:
        explanation = LLMExplanationService.generate_explanation(evidence)
    except Exception as e:
        logger.warning(f"Gemini LLM unavailable ({e}). Using deterministic structured synthesis.")
        explanation = ""
        
    if not explanation or "Failed" in explanation or "Key not configured" in explanation:
        # Structured deterministic fallback narrative
        level = state["risk_level"]
        score = state["risk_score"]
        drivers_text = "\n".join([f"- **{d['display_name']}**: {d['description']} ({d['contribution_pct']}% impact)" for d in state["risk_drivers"][:4]])
        recs_text = "\n".join([f"- {r}" for r in state["recommendations"][:4]])
        
        explanation = f"""### Executive Risk Summary: {level} Risk ({score:.2f})

Release **{req.get('release')}** for **{req.get('repository')}** has been evaluated across Code, Test, Defect, and Operations telemetry by ReleaseShield's Hybrid Risk Engine.

#### Primary Risk Drivers:
{drivers_text}

#### Agent Findings Breakdown:
- **Code Agent**: {state['code_result']['summary']}
- **Test Agent**: {state['test_result']['summary']}
- **Defect Agent**: {state['defect_result']['summary']}
- **Operations Agent**: {state['ops_result']['summary']}

#### Key Actionable Recommendations:
{recs_text}

> **Governance Notice**: ReleaseShield provides release readiness advisory only and cannot execute automated deployments. Human approval sign-off is mandatory before deployment."""

    return {"explanation": explanation}

async def finalize_unified_report_node(state: MultiAgentState) -> MultiAgentState:
    req = state["request"]
    repo = req.get("repository", "")
    release = req.get("release", "")
    
    approval = ApprovalService.get_approval(repo, release)
    
    summary = f"Release {release} evaluated as {state['risk_level']} risk with score {state['risk_score']:.2f} across all 4 domain agents."
    
    report = UnifiedRiskReport(
        repository=repo,
        release=release,
        release_type=ReleaseType(req.get("release_type", "MINOR")),
        target_environment=req.get("target_environment", "production"),
        scenario=req.get("scenario", "standard_healthy"),
        risk_score=state["risk_score"],
        risk_level=Severity(state["risk_level"]),
        confidence=state["confidence"],
        trend=RiskTrend(state["trend"]),
        summary=summary,
        hybrid_engine=HybridEngineBreakdown(**state["hybrid_engine"]),
        risk_drivers=[RiskDriver(**d) for d in state["risk_drivers"]],
        code_agent=AgentResult(**state["code_result"]),
        test_agent=AgentResult(**state["test_result"]),
        defect_agent=AgentResult(**state["defect_result"]),
        operations_agent=AgentResult(**state["ops_result"]),
        recommendations=state["recommendations"],
        required_actions=[RequiredAction(**a) for a in state["required_actions"]],
        explanation=state["explanation"],
        approval=approval
    )
    
    return {"final_report": report.model_dump()}

# -------------------------------------------------------------
# Graph Builder
# -------------------------------------------------------------

def create_multi_agent_orchestrator():
    workflow = StateGraph(MultiAgentState)
    
    workflow.add_node("gather_adapter_data", gather_adapter_data_node)
    workflow.add_node("run_domain_agents", run_domain_agents_node)
    workflow.add_node("run_hybrid_risk_engine", run_hybrid_risk_engine_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    workflow.add_node("generate_explanation", generate_explanation_node)
    workflow.add_node("finalize_unified_report", finalize_unified_report_node)
    
    workflow.set_entry_point("gather_adapter_data")
    workflow.add_edge("gather_adapter_data", "run_domain_agents")
    workflow.add_edge("run_domain_agents", "run_hybrid_risk_engine")
    workflow.add_edge("run_hybrid_risk_engine", "generate_recommendations")
    workflow.add_edge("generate_recommendations", "generate_explanation")
    workflow.add_edge("generate_explanation", "finalize_unified_report")
    workflow.add_edge("finalize_unified_report", END)
    
    return workflow.compile()
