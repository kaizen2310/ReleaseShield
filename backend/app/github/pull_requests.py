from typing import List, Dict, Any
from app.github.client import github_client
from app.github.commits import compare_commits

async def get_pull_requests_for_commits(owner: str, repo: str, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of commits, attempts to find the PRs associated with them.
    A simple approach for the MVP: Look at merge commits.
    Merge commits usually have messages like 'Merge pull request #123 from ...'
    or '... (#123)' for squash merges.
    """
    # Note: A more robust approach uses the search API or GraphQL API.
    # For MVP, we will fetch PRs closed in the general time window or search by commit hash.
    # To save API limits, if we just want closed PRs in the release timeframe:
    # We will search PRs based on standard methods. For now, this is a placeholder.
    pass

async def get_pull_request(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    response = await github_client.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")
    return response.json()

async def get_pull_request_files(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    return await github_client.get_paginated(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
