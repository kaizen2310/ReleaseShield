from langgraph.graph import StateGraph, END
from app.agents.git_agent.state import GitAgentState
from app.agents.git_agent.nodes import (
    validate_input_node,
    fetch_release_data_node,
    collect_git_data_node,
    calculate_features_node,
    load_historical_baseline_node,
    analyze_anomalies_node,
    calculate_risk_node,
    generate_recommendations_node,
    generate_llm_explanation_node,
    evidence_critic_node,
    finalize_report_node
)

def create_git_agent_workflow():
    workflow = StateGraph(GitAgentState)

    # Add nodes
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("fetch_release", fetch_release_data_node)
    workflow.add_node("collect_git_data", collect_git_data_node)
    workflow.add_node("calculate_features", calculate_features_node)
    workflow.add_node("load_historical_baseline", load_historical_baseline_node)
    workflow.add_node("analyze_anomalies", analyze_anomalies_node)
    workflow.add_node("calculate_risk", calculate_risk_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    workflow.add_node("generate_llm_explanation", generate_llm_explanation_node)
    workflow.add_node("evidence_critic", evidence_critic_node)
    workflow.add_node("finalize_report", finalize_report_node)

    # Edge definitions with error handling
    def should_continue(state: GitAgentState) -> str:
        if "error" in state and state["error"]:
            return "finalize_report" # Jump to end on error
        return "continue"

    workflow.set_entry_point("validate_input")
    
    workflow.add_conditional_edges("validate_input", should_continue, {"continue": "fetch_release", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("fetch_release", should_continue, {"continue": "collect_git_data", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("collect_git_data", should_continue, {"continue": "calculate_features", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("calculate_features", should_continue, {"continue": "load_historical_baseline", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("load_historical_baseline", should_continue, {"continue": "analyze_anomalies", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("analyze_anomalies", should_continue, {"continue": "calculate_risk", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("calculate_risk", should_continue, {"continue": "generate_recommendations", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("generate_recommendations", should_continue, {"continue": "generate_llm_explanation", "finalize_report": "finalize_report"})
    workflow.add_conditional_edges("generate_llm_explanation", should_continue, {"continue": "evidence_critic", "finalize_report": "finalize_report"})
    
    def should_accept_explanation(state: GitAgentState) -> str:
        if "error" in state and state["error"]:
            return "finalize_report"
        if state.get("critic_feedback"):
            return "generate_llm_explanation"
        return "finalize_report"
        
    workflow.add_conditional_edges("evidence_critic", should_accept_explanation, {
        "generate_llm_explanation": "generate_llm_explanation", 
        "finalize_report": "finalize_report"
    })
    
    workflow.add_edge("finalize_report", END)

    return workflow.compile()
