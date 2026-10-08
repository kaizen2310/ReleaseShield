import os
import json
from typing import Optional, Dict, Any

class GitHubCache:
    CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/raw/github"))
    
    @staticmethod
    def _get_filename(owner: str, repo: str, endpoint: str) -> str:
        safe_endpoint = endpoint.replace("/", "_").replace("?", "_").replace("=", "_")
        return os.path.join(GitHubCache.CACHE_DIR, f"{owner}_{repo}_{safe_endpoint}.json")
        
    @staticmethod
    def get(owner: str, repo: str, endpoint: str) -> Optional[Dict[str, Any]]:
        filename = GitHubCache._get_filename(owner, repo, endpoint)
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return None
        
    @staticmethod
    def set(owner: str, repo: str, endpoint: str, data: Any):
        os.makedirs(GitHubCache.CACHE_DIR, exist_ok=True)
        filename = GitHubCache._get_filename(owner, repo, endpoint)
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: failed to write cache for {endpoint}: {e}")
