import sys
import os
import argparse
import asyncio

from app.db.database import Base, engine, SessionLocal
from app.agents.git_agent.workflow import create_git_agent_workflow
from app.agents.git_agent.state import GitAgentState
from app.github.releases import get_all_releases


async def process_release(agent, owner: str, name: str, tag_name: str, previous_tag: str):
    print(f"Processing release {tag_name} (baseline: {previous_tag})...")
    initial_state = GitAgentState(
        repository=f"{owner}/{name}",
        target_release=tag_name,
        historical_window=10,
        previous_release=previous_tag
    )
    final_state = await agent.ainvoke(initial_state)
    if "error" in final_state and final_state["error"]:
        print(f"Error processing {tag_name}: {final_state['error']}")
    else:
        print(f"Successfully processed {tag_name}")

async def main():
    parser = argparse.ArgumentParser(description="Collect historical releases for ReleaseShield")
    parser.add_argument("--repository", required=True, help="Repository name (e.g. facebook/react)")
    parser.add_argument("--releases", type=int, default=10, help="Number of historical releases to collect")
    args = parser.parse_args()
    
    agent = create_git_agent_workflow()
    owner, name = args.repository.split("/")
    
    print(f"Fetching releases for {args.repository}...")
    releases = await get_all_releases(owner, name, limit=args.releases + 1)
    
    if len(releases) < 2:
        print("Not enough releases found to establish a baseline.")
        return
        
    releases.sort(key=lambda x: x.get("published_at") or x.get("created_at", ""), reverse=True)
    
    valid_releases = [r for r in releases if not r.get("draft") and not r.get("prerelease")]
    
    target_count = min(args.releases, len(valid_releases) - 1)
    
    for i in range(target_count):
        current = valid_releases[i]
        previous = valid_releases[i+1]
        await process_release(agent, owner, name, current["tag_name"], previous["tag_name"])

    print("Finished seeding the database.")

if __name__ == "__main__":
    asyncio.run(main())
