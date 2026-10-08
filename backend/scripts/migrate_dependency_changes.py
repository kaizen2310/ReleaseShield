import sys
import os

from sqlalchemy import text
from app.db.database import engine

def add_column():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE git_metrics ADD COLUMN dependency_changes INTEGER DEFAULT 0 NOT NULL;"))
            print("Successfully added dependency_changes column.")
        except Exception as e:
            print(f"Failed to add column (it might already exist): {e}")

if __name__ == "__main__":
    add_column()
