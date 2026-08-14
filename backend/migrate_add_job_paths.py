"""
Quick migration script to add output file path columns to the jobs table.
Run once, then delete.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from database import engine
from sqlalchemy import text

NEW_COLUMNS = [
    ("midi_file_path", "VARCHAR"),
    ("piano_audio_path", "VARCHAR"),
    ("vocals_file_path", "VARCHAR"),
    ("backing_file_path", "VARCHAR"),
    ("transcription_file_path", "VARCHAR"),
    ("srt_file_path", "VARCHAR"),
    ("lrc_file_path", "VARCHAR"),
    ("ass_file_path", "VARCHAR"),
    ("final_video_path", "VARCHAR"),
    ("thumbnail_path", "VARCHAR"),
]

def migrate():
    for col_name, col_type in NEW_COLUMNS:
        # Use a fresh connection per column so one failure doesn't abort the rest
        with engine.connect() as conn:
            try:
                conn.execute(text(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                conn.commit()
                print(f"  [OK] Added column: {col_name}")
            except Exception as e:
                conn.rollback()
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  [SKIP] Column already exists: {col_name}")
                else:
                    print(f"  [ERR] Error adding {col_name}: {e}")
    print("\nMigration complete!")

if __name__ == "__main__":
    print("Adding output file path columns to jobs table...")
    migrate()
