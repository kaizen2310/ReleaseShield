import httpx
from typing import Any, Dict, List, Optional
from app.config import settings

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        async with httpx.AsyncClient(headers=self.headers, base_url=self.base_url, follow_redirects=True) as client:
            response = await client.request(method, endpoint, params=params)
            response.raise_for_status()
            return response

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> httpx.Response:
        from app.github.cache import GitHubCache
        
        # Determine owner/repo context if possible for cache naming
        parts = endpoint.strip("/").split("/")
        owner, repo = ("unknown", "unknown")
        if len(parts) >= 3 and parts[0] == "repos":
            owner, repo = parts[1], parts[2]
            
        cache_key = endpoint
        if params:
            cache_key += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
            
        if use_cache:
            cached_data = GitHubCache.get(owner, repo, cache_key)
            if cached_data is not None:
                # Mock a response object
                class MockResponse:
                    def __init__(self, data, cached_headers):
                        self.data = data
                        self.headers = cached_headers
                    def json(self): return self.data
                
                # Try to retrieve cached headers if available, otherwise mock empty
                cached_headers_dict = GitHubCache.get(owner, repo, cache_key + "_headers") or {}
                return MockResponse(cached_data, cached_headers_dict)

        response = await self._request("GET", endpoint, params)
        data = response.json()
        
        if use_cache:
            GitHubCache.set(owner, repo, cache_key, data)
            GitHubCache.set(owner, repo, cache_key + "_headers", dict(response.headers))
            
        return response

    async def get_paginated(self, endpoint: str, params: Optional[Dict[str, Any]] = None, max_pages: int = 5) -> List[Dict[str, Any]]:
        results = []
        current_page = 1
        
        if not params:
            params = {}
        
        params["per_page"] = 100
        
        while current_page <= max_pages:
            params["page"] = current_page
            try:
                response = await self.get(endpoint, params)
                data = response.json()
                
                if not data:
                    break
                    
                results.extend(data)
                
                if "next" not in response.headers.get("Link", ""):
                    break
                    
                current_page += 1
            except httpx.HTTPError:
                break
                
        return results

github_client = GitHubClient()
