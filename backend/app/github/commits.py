from typing import Dict, Any, List
from app.github.client import github_client

async def compare_commits(owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
    """
    Compare two commits/tags. Returns standard compare payload.
    """
    response = await github_client.get(f"/repos/{owner}/{repo}/compare/{base}...{head}")
    return response.json()

async def get_commit(owner: str, repo: str, sha: str) -> Dict[str, Any]:
    response = await github_client.get(f"/repos/{owner}/{repo}/commits/{sha}")
    return response.json()
