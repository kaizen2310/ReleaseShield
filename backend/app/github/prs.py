from typing import Dict, Any, List
from app.github.client import github_client
from urllib.parse import quote

async def get_prs_between_dates(owner: str, repo: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Use GitHub Search API to find merged PRs between two dates.
    Dates should be in ISO8601 format (e.g. 2026-10-08T00:00:00Z)
    """
    query = f"repo:{owner}/{repo} is:pr is:merged merged:{start_date}..{end_date}"
    encoded_query = quote(query)
    
    # Use the paginated client on the search endpoint
    endpoint = "/search/issues"
    
    # The search endpoint returns {"total_count": X, "items": [...]}
    # We need a custom pagination for search or just fetch the first few pages
    # Let's manually fetch a few pages
    results = []
    current_page = 1
    max_pages = 5
    
    while current_page <= max_pages:
        try:
            response = await github_client.get(endpoint, {"q": query, "per_page": 100, "page": current_page})
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                break
                
            results.extend(items)
            
            if "next" not in response.headers.get("Link", ""):
                break
                
            current_page += 1
        except Exception:
            break
            
    # Search API issues don't have additions/deletions. We might need to fetch the PR details individually
    # but for rate limiting reasons, we will only fetch details if it's less than ~50 PRs, or just use the issue data.
    # The issue data includes created_at and closed_at/merged_at which is enough for merge time.
    # To get additions/deletions, we need the PR endpoint. 
    
    pr_details = []
    for pr in results[:50]: # Limit to 50 PR detail fetches to avoid rate limit
        try:
            pr_response = await github_client.get(f"/repos/{owner}/{repo}/pulls/{pr['number']}")
            pr_details.append(pr_response.json())
        except Exception:
            pass

    return pr_details
