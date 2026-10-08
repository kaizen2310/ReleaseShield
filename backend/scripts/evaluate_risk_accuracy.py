import sys
import os
import argparse
import asyncio
from datetime import timedelta

from app.db.database import SessionLocal
from app.models.repository import Repository
from app.models.release import Release
from app.models.risk_assessment import RiskAssessmentDB

def evaluate_accuracy(owner: str, name: str):
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.owner == owner, Repository.name == name).first()
        if not repo:
            print("Repository not found in DB. Run collection first.")
            return

        # Fetch all evaluated releases
        assessments = db.query(RiskAssessmentDB).join(RiskAssessmentDB.release).filter(
            Release.repository_id == repo.id
        ).order_by(Release.published_at.desc()).all()

        if not assessments:
            print("No risk assessments found.")
            return

        releases = db.query(Release).filter(Release.repository_id == repo.id).order_by(Release.published_at.desc()).all()
        
        print(f"Evaluating Risk Accuracy for {owner}/{name}")
        print("-" * 50)
        
        for assessment in assessments:
            release = assessment.release
            if not release.published_at:
                continue
                
            # Find if there is a hotfix within 14 days
            # A hotfix is a release that comes after this one, but before the next minor/major
            # For simplicity, we just look for any release within 14 days of this release's publication
            hotfixes = []
            for r in releases:
                if r.id == release.id or not r.published_at:
                    continue
                if r.published_at > release.published_at and (r.published_at - release.published_at) <= timedelta(days=14):
                    hotfixes.append(r)
            
            # Outcome: 1 if hotfixed, 0 otherwise
            actual_risk = len(hotfixes) > 0
            predicted_risk = assessment.risk_level in ["HIGH", "CRITICAL"]
            
            status = "MATCH" if actual_risk == predicted_risk else "MISMATCH"
            
            print(f"Release: {release.tag_name:<15} | Score: {assessment.risk_score:<4.2f} ({assessment.risk_level:<6}) | "
                  f"Subsequent Hotfixes: {len(hotfixes)} | {status}")
                  
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate risk score accuracy against actual hotfixes.")
    parser.add_argument("--repository", required=True, help="Repository name (e.g. facebook/react)")
    args = parser.parse_args()
    
    owner, name = args.repository.split("/")
    evaluate_accuracy(owner, name)
