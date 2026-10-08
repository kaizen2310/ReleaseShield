import sys
import os
import asyncio
import argparse

# Add the backend directory to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.db.database import SessionLocal, Base, engine
from app.models.repository import Repository
from app.models.release import Release
from app.models.git_metrics import GitMetricsDB
from app.github.releases import get_all_releases
from app.services.github_service import GitHubService
from app.services.metrics_service import MetricsService
from app.utils.dates import parse_github_date

async def collect_historical_data(owner: str, repo_name: str, num_releases: int):
    # Ensure tables exist for MVP (in production use Alembic)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Ensure repository exists
        db_repo = db.query(Repository).filter(Repository.owner == owner, Repository.name == repo_name).first()
        if not db_repo:
            db_repo = Repository(owner=owner, name=repo_name)
            db.add(db_repo)
            db.commit()
            db.refresh(db_repo)
            
        # 2. Fetch releases from GitHub
        print(f"Fetching releases for {owner}/{repo_name}...")
        github_releases = await get_all_releases(owner, repo_name, limit=num_releases + 5)
        
        # Filter out drafts and prereleases
        valid_releases = [r for r in github_releases if not r.get("draft") and not r.get("prerelease")]
        valid_releases = valid_releases[:num_releases]
        
        print(f"Found {len(valid_releases)} valid releases to process.")
        
        for i, target_release in enumerate(valid_releases):
            tag = target_release["tag_name"]
            
            # Check if already in DB
            existing_release = db.query(Release).filter(
                Release.repository_id == db_repo.id, 
                Release.tag_name == tag
            ).first()
            
            if existing_release:
                print(f"[{i+1}/{len(valid_releases)}] Release {tag} already collected. Skipping.")
                continue
                
            print(f"[{i+1}/{len(valid_releases)}] Processing release {tag}...")
            
            try:
                # Fetch detailed data (this also finds the previous release)
                raw_data = await GitHubService.get_release_data(owner, repo_name, tag)
                
                # Calculate metrics
                metrics = MetricsService.calculate_metrics(raw_data)
                
                # Save Release
                db_release = Release(
                    repository_id=db_repo.id,
                    tag_name=tag,
                    previous_tag=raw_data["previous_release"]["tag_name"],
                    published_at=parse_github_date(target_release.get("published_at"))
                )
                db.add(db_release)
                db.flush() # get id
                
                # Save Metrics
                db_metrics = GitMetricsDB(
                    release_id=db_release.id,
                    **metrics.model_dump()
                )
                db.add(db_metrics)
                db.commit()
                
                print(f"  -> Successfully stored metrics for {tag} (Churn: {metrics.code_churn})")
            except Exception as e:
                print(f"  -> Failed to process {tag}: {e}")
                db.rollback()
                
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect historical releases for a GitHub repository")
    parser.add_argument("--repository", type=str, required=True, help="Format: owner/repo")
    parser.add_argument("--releases", type=int, default=10, help="Number of historical releases to collect")
    
    args = parser.parse_args()
    
    try:
        owner, repo = args.repository.split("/")
    except ValueError:
        print("Invalid repository format. Please use owner/repo")
        sys.exit(1)
        
    asyncio.run(collect_historical_data(owner, repo, args.releases))
