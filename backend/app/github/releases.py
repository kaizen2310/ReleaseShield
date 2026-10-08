from typing import Dict, Any, Optional
from app.github.client import github_client
from httpx import HTTPStatusError

async def get_repository(owner: str, repo: str) -> Dict[str, Any]:
    response = await github_client.get(f"/repos/{owner}/{repo}")
    return response.json()

async def get_release_by_tag(owner: str, repo: str, tag: str) -> Dict[str, Any]:
    try:
        response = await github_client.get(f"/repos/{owner}/{repo}/releases/tags/{tag}")
        return response.json()
    except HTTPStatusError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Release or tag '{tag}' not found in {owner}/{repo}")
        raise

async def get_all_releases(owner: str, repo: str, limit: int = 30) -> list[Dict[str, Any]]:
    # Just fetch one page of 100 for now to find previous releases
    response = await github_client.get(f"/repos/{owner}/{repo}/releases", params={"per_page": min(limit, 100)})
    return response.json()

async def get_previous_release(owner: str, repo: str, current_tag: str) -> Optional[Dict[str, Any]]:
    releases = await get_all_releases(owner, repo, limit=100)
    
    # Sort releases by published_at or created_at descending just to be sure
    releases.sort(key=lambda x: x.get("published_at") or x.get("created_at", ""), reverse=True)
    
    found_current = False
    for r in releases:
        if r.get("tag_name") == current_tag:
            found_current = True
            continue
        
        if found_current and not r.get("draft") and not r.get("prerelease"):
            return r
            
    return None
