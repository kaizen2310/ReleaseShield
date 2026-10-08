from app.agents.git_agent.state import GitAgentState
from app.services.github_service import GitHubService
from app.services.metrics_service import MetricsService
from app.services.baseline_service import BaselineService
from app.services.risk_service import RiskService
from app.db.database import SessionLocal
from app.models.risk_assessment import RiskAssessmentDB
from app.models.repository import Repository
from app.services.persistence_service import PersistenceService
import dateutil.parser

async def validate_input_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: validate_input")
    repo = state.get("repository", "")
    if "/" not in repo:
        return {"error": "Invalid repository format. Must be owner/name."}
    if not state.get("target_release"):
        return {"error": "Target release must be specified."}
    
    return state

async def fetch_release_data_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: fetch_release_data")
    if "error" in state: return state
    
    owner, name = state["repository"].split("/")
    tag = state["target_release"]
    
    try:
        raw_data = await GitHubService.get_release_data(owner, name, tag)
        return {
            "release_metadata": raw_data,
            "previous_release": raw_data["previous_release"]["tag_name"]
        }
    except Exception as e:
        return {"error": f"Failed to fetch release data: {str(e)}"}

async def collect_git_data_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: collect_git_data")
    if "error" in state: return state
    
    raw_data = state["release_metadata"]
    owner, name = state["repository"].split("/")
    
    target_date = raw_data["target_release"].get("published_at") or raw_data["target_release"].get("created_at")
    previous_date = raw_data["previous_release"].get("published_at") or raw_data["previous_release"].get("created_at")
    
    pull_requests = []
    if target_date and previous_date:
        try:
            from app.github.prs import get_prs_between_dates
            pull_requests = await get_prs_between_dates(owner, name, previous_date, target_date)
        except Exception as e:
            print(f"Failed to fetch PRs: {e}")

    return {
        "commits": raw_data["comparison"].get("commits", []),
        "changed_files": raw_data["comparison"].get("files", []),
        "pull_requests": pull_requests
    }

async def calculate_features_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: calculate_features")
    if "error" in state: return state
    
    try:
        metrics = MetricsService.calculate_metrics(state["release_metadata"], state["pull_requests"])
        return {"current_metrics": metrics}
    except Exception as e:
        return {"error": f"Failed to calculate metrics: {str(e)}"}

async def load_historical_baseline_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: load_historical_baseline")
    if "error" in state: return state
    
    owner, name = state["repository"].split("/")
    window = state.get("historical_window", 10)
    
    db = SessionLocal()
    try:
        historical_metrics = BaselineService.get_historical_metrics(db, owner, name, limit=window)
        return {"historical_metrics": historical_metrics}
    finally:
        db.close()

async def analyze_anomalies_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: analyze_anomalies")
    if "error" in state: return state
    
    owner, name = state["repository"].split("/")
    tag = state["target_release"]
    current = state["current_metrics"]
    historical = state["historical_metrics"]
    
    try:
        baseline_analysis = BaselineService.analyze_baseline(owner, name, tag, current, historical)
        findings = RiskService.analyze_anomalies(baseline_analysis)
        
        return {
            "baseline_analysis": baseline_analysis,
            "risk_signals": findings
        }
    except Exception as e:
        return {"error": f"Failed to analyze baseline: {str(e)}"}

async def calculate_risk_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: calculate_risk")
    if "error" in state: return state
    
    owner, name = state["repository"].split("/")
    
    # We could fetch previous risk scores from DB for trend analysis
    db = SessionLocal()
    previous_scores = []
    try:
        repo = db.query(Repository).filter(Repository.owner == owner, Repository.name == name).first()
        if repo:
            past_assessments = db.query(RiskAssessmentDB).join(RiskAssessmentDB.release).filter(
                RiskAssessmentDB.release.has(repository_id=repo.id)
            ).order_by(RiskAssessmentDB.id.desc()).limit(3).all()
            previous_scores = [a.risk_score for a in past_assessments]
    finally:
        db.close()

    try:
        assessment = RiskService.evaluate_release(state["baseline_analysis"], previous_scores)
        
        return {
            "risk_score": assessment.risk_score,
            "risk_level": assessment.risk_level,
            "confidence": assessment.confidence,
            "trend": assessment.trend,
            "findings": assessment.findings
        }
    except Exception as e:
        return {"error": f"Failed to calculate risk: {str(e)}"}

async def generate_recommendations_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: generate_recommendations")
    if "error" in state: return state
    
    findings = state.get("findings", [])
    recommendations = []
    
    for f in findings:
        if f.category == "CODE_CHURN":
            recommendations.append("Review high-churn files for potential bugs or technical debt.")
        elif f.category == "CHANGE_SCOPE":
            recommendations.append("Perform extended regression testing due to the large surface area of changes.")
        elif f.category == "COMMIT_ACTIVITY":
            recommendations.append("Ensure rapid commits are well-reviewed; check for potential 'rush-to-release' behavior.")
            
    if not recommendations:
        recommendations.append("No significant anomalies detected. Standard release procedures apply.")
        
    return {"recommendations": recommendations}

async def generate_llm_explanation_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: generate_llm_explanation")
    if "error" in state: return state
    
    from app.llm.explanation_service import LLMExplanationService
    
    evidence = {
        "repository": state.get("repository"),
        "release": state.get("target_release"),
        "risk_score": state.get("risk_score"),
        "risk_level": state.get("risk_level", "").value if hasattr(state.get("risk_level"), "value") else state.get("risk_level"),
        "trend": state.get("trend", "").value if hasattr(state.get("trend"), "value") else state.get("trend"),
        "confidence": state.get("confidence"),
        "findings": [f.model_dump() for f in state.get("findings", [])],
        "recommendations": state.get("recommendations", [])
    }
    
    # If the critic rejected the previous explanation, pass the feedback
    if state.get("critic_feedback"):
        evidence["critic_feedback"] = state["critic_feedback"]
    
    explanation = LLMExplanationService.generate_explanation(evidence)
    return {"llm_explanation": explanation}

async def evidence_critic_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: evidence_critic")
    if "error" in state: return state
    
    from app.llm.critic_service import CriticService
    
    retries = state.get("retries", 0)
    
    # Max retries to prevent infinite loops
    if retries >= 2:
        print("Max critic retries reached. Accepting current explanation.")
        return state
        
    validation = CriticService.validate_explanation(
        explanation=state.get("llm_explanation", ""),
        findings=[f.model_dump() for f in state.get("findings", [])],
        risk_score=state.get("risk_score", 0.0)
    )
    
    if not validation["valid"]:
        print(f"Critic rejected explanation: {validation['feedback']}")
        return {
            "critic_feedback": validation["feedback"],
            "retries": retries + 1
        }
        
    print("Critic approved explanation.")
    return {"critic_feedback": ""} # Clear feedback if valid

async def finalize_report_node(state: GitAgentState) -> GitAgentState:
    print(f"Node: finalize_report")
    if "error" in state and state["error"]:
        return state

    # Persist data
    db = SessionLocal()
    try:
        owner, name = state["repository"].split("/")
        repo = PersistenceService.get_or_create_repository(db, owner, name)
        
        release_metadata = state.get("release_metadata", {})
        published_at_str = release_metadata.get("target_release", {}).get("published_at")
        published_at = dateutil.parser.parse(published_at_str) if published_at_str else None
        
        release = PersistenceService.get_or_create_release(
            db=db,
            repository_id=repo.id,
            tag_name=state["target_release"],
            previous_tag=state.get("previous_release"),
            published_at=published_at
        )
        
        if "current_metrics" in state:
            PersistenceService.persist_metrics(db, release.id, state["current_metrics"])
            
        if "risk_score" in state:
            PersistenceService.persist_risk_assessment(
                db=db,
                release_id=release.id,
                risk_score=state["risk_score"],
                risk_level=state.get("risk_level", "").value if hasattr(state.get("risk_level"), "value") else state.get("risk_level"),
                confidence=state.get("confidence", 0.0),
                trend=state.get("trend", "").value if hasattr(state.get("trend"), "value") else state.get("trend"),
                findings=state.get("findings", []),
                llm_explanation=state.get("llm_explanation")
            )
    except Exception as e:
        print(f"Failed to persist report: {e}")
    finally:
        db.close()
        
    return state
