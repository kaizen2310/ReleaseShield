from typing import Dict, Any
from app.github import releases, commits

class GitHubService:
    @staticmethod
    async def get_release_data(owner: str, repo: str, tag: str) -> Dict[str, Any]:
        target_release = await releases.get_release_by_tag(owner, repo, tag)
        previous_release = await releases.get_previous_release(owner, repo, tag)
        
        if not previous_release:
            raise ValueError("Could not determine a previous release to establish a baseline.")
            
        previous_tag = previous_release["tag_name"]
        
        comparison = await commits.compare_commits(owner, repo, previous_tag, tag)
        
        return {
            "repository": f"{owner}/{repo}",
            "target_release": target_release,
            "previous_release": previous_release,
            "comparison": comparison
        }
