"""
Database schema migration — Add thought evolution tracking fields to nodes table.

Run this script ONCE to update the schema:
    python scripts/migrate_schema.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.services.snowflake_service import _get_connection
from app.config import settings
from app.utils.logger import logger


def migrate_schema():
    """Add evolution tracking columns to nodes table."""

    logger.info("Starting schema migration...")

    conn = _get_connection()
    cursor = conn.cursor()

    # Set database and schema context
    cursor.execute(f"USE DATABASE {settings.snowflake_database}")
    cursor.execute(f"USE SCHEMA {settings.snowflake_schema}")

    try:
        # Check if columns already exist
        cursor.execute("""
            SELECT COUNT(*) as col_count
            FROM information_schema.columns
            WHERE table_name = 'NODES'
            AND column_name IN ('PRIMARY_TEXT', 'ACCUMULATED_TEXT', 'MERGE_COUNT',
                               'EVOLUTION_HISTORY', 'CONTRIBUTORS', 'CREATIVITY_SCORE', 'LAST_UPDATED')
        """)

        result = cursor.fetchone()
        existing_cols = result[0] if result else 0

        if existing_cols == 7:
            logger.info("Schema migration already applied. Skipping.")
            return

        logger.info("Adding evolution tracking columns...")

        # Add new columns (Snowflake doesn't support multiple columns in one ALTER TABLE)
        alterations = [
            "ALTER TABLE nodes ADD COLUMN primary_text STRING",
            "ALTER TABLE nodes ADD COLUMN accumulated_text STRING",
            "ALTER TABLE nodes ADD COLUMN merge_count NUMBER DEFAULT 0",
            "ALTER TABLE nodes ADD COLUMN evolution_history VARIANT",  # JSON array
            "ALTER TABLE nodes ADD COLUMN contributors VARIANT",  # JSON array
            "ALTER TABLE nodes ADD COLUMN creativity_score FLOAT DEFAULT 0.0",
            "ALTER TABLE nodes ADD COLUMN last_updated NUMBER DEFAULT 0",
        ]

        for sql in alterations:
            try:
                cursor.execute(sql)
                logger.info(f"  ✓ {sql.split('ADD COLUMN')[1].split()[0]}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"  - Column already exists, skipping")
                else:
                    raise

        # Backfill existing nodes with default values
        logger.info("Backfilling existing nodes...")
        cursor.execute("""
            UPDATE nodes
            SET
                primary_text = COALESCE(primary_text, text),
                accumulated_text = COALESCE(accumulated_text, text),
                merge_count = COALESCE(merge_count, 0),
                evolution_history = COALESCE(evolution_history, PARSE_JSON('[]')),
                contributors = COALESCE(contributors, PARSE_JSON('[]')),
                creativity_score = COALESCE(creativity_score, 0.0),
                last_updated = COALESCE(last_updated, timestamp)
            WHERE primary_text IS NULL
        """)

        affected_rows = cursor.rowcount
        logger.info(f"Backfilled {affected_rows} existing nodes")

        conn.commit()
        logger.info("✓ Schema migration completed successfully!")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise

    finally:
        cursor.close()


if __name__ == "__main__":
    migrate_schema()
