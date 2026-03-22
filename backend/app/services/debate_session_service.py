"""
Debate session service — Manage debate session creation and storage.
"""

from typing import List, Optional
from uuid import uuid4
import json as json_module

from app.models.debate import (
    DebateSession,
    DebateSessionParticipant,
    CreateDebateSessionRequest,
    DebateSessionResponse,
)
from app.services.snowflake_service import _get_connection, async_snowflake, _execute_non_query
from app.utils.time_utils import now_timestamp
from app.utils.logger import logger


@async_snowflake
def _create_session_table_if_not_exists() -> None:
    """
    Create the debate_sessions table if it doesn't exist.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    sql = """
        CREATE TABLE IF NOT EXISTS debate_sessions (
            session_id VARCHAR(36) PRIMARY KEY,
            topic_name VARCHAR(500) NOT NULL,
            creator_wallet VARCHAR(200) NOT NULL,
            creator_names VARIANT NOT NULL,
            participants VARIANT NOT NULL,
            created_at BIGINT NOT NULL,
            status VARCHAR(20) DEFAULT 'active',
            total_contributions INT DEFAULT 0
        )
    """

    try:
        cursor.execute(sql)
        # Add table comment after creation
        comment_sql = """
            COMMENT ON TABLE debate_sessions IS
            'Debate session metadata. Participants array contains objects with optional name and required wallet_address'
        """
        cursor.execute(comment_sql)
        logger.info("Debate sessions table ready")
    except Exception as error:
        logger.error(f"Failed to create debate_sessions table: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


@async_snowflake
def _insert_session_sync(session: DebateSession) -> None:
    """
    Insert a new debate session into the database.

    Args:
        session: DebateSession to insert
    """
    sql = """
        INSERT INTO debate_sessions (
            session_id,
            topic_name,
            creator_wallet,
            creator_names,
            participants,
            created_at,
            status,
            total_contributions
        )
        SELECT
            %(session_id)s,
            %(topic_name)s,
            %(creator_wallet)s,
            PARSE_JSON(%(creator_names)s),
            PARSE_JSON(%(participants)s),
            %(created_at)s,
            %(status)s,
            %(total_contributions)s
    """

    params = {
        'session_id': session.session_id,
        'topic_name': session.topic_name,
        'creator_wallet': session.creator_wallet,
        'creator_names': json_module.dumps(session.creator_names),
        'participants': json_module.dumps([p.dict() for p in session.participants]),
        'created_at': session.created_at,
        'status': session.status,
        'total_contributions': session.total_contributions,
    }

    _execute_non_query(sql, params)
    logger.info(f"Debate session inserted: {session.session_id}")


async def insert_session(session: DebateSession) -> None:
    """Insert a debate session (async)."""
    await _insert_session_sync(session)


@async_snowflake
def _get_session_by_id_sync(session_id: str) -> Optional[DebateSession]:
    """
    Get a debate session by ID.

    Args:
        session_id: Session ID

    Returns:
        DebateSession or None if not found
    """
    conn = _get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            session_id,
            topic_name,
            creator_wallet,
            creator_names,
            participants,
            created_at,
            status,
            total_contributions
        FROM debate_sessions
        WHERE session_id = %(session_id)s
    """

    try:
        cursor.execute(sql, {'session_id': session_id})
        row = cursor.fetchone()

        if not row:
            return None

        # Parse JSON fields
        creator_names_data = row[3]
        if isinstance(creator_names_data, str):
            creator_names_data = json_module.loads(creator_names_data)

        participants_data = row[4]
        if isinstance(participants_data, str):
            participants_data = json_module.loads(participants_data)

        participants = [DebateSessionParticipant(**p) for p in participants_data]

        return DebateSession(
            session_id=row[0],
            topic_name=row[1],
            creator_wallet=row[2],
            creator_names=creator_names_data,
            participants=participants,
            created_at=row[5],
            status=row[6],
            total_contributions=row[7],
        )

    except Exception as error:
        logger.error(f"Failed to fetch session {session_id}: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


async def get_session_by_id(session_id: str) -> Optional[DebateSession]:
    """Get a debate session by ID (async)."""
    return await _get_session_by_id_sync(session_id)


@async_snowflake
def _get_all_sessions_sync() -> List[DebateSession]:
    """
    Get all debate sessions.

    Returns:
        List of DebateSession
    """
    conn = _get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT
            session_id,
            topic_name,
            creator_wallet,
            creator_names,
            participants,
            created_at,
            status,
            total_contributions
        FROM debate_sessions
        ORDER BY created_at DESC
    """

    try:
        cursor.execute(sql)
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            # Parse JSON fields
            creator_names_data = row[3]
            if isinstance(creator_names_data, str):
                creator_names_data = json_module.loads(creator_names_data)

            participants_data = row[4]
            if isinstance(participants_data, str):
                participants_data = json_module.loads(participants_data)

            participants = [DebateSessionParticipant(**p) for p in participants_data]

            sessions.append(DebateSession(
                session_id=row[0],
                topic_name=row[1],
                creator_wallet=row[2],
                creator_names=creator_names_data,
                participants=participants,
                created_at=row[5],
                status=row[6],
                total_contributions=row[7],
            ))

        return sessions

    except Exception as error:
        logger.error(f"Failed to fetch all sessions: {error}")
        raise
    finally:
        cursor.close()
        conn.close()


async def get_all_sessions() -> List[DebateSession]:
    """Get all debate sessions (async)."""
    return await _get_all_sessions_sync()


async def create_debate_session(
    request: CreateDebateSessionRequest
) -> DebateSessionResponse:
    """
    Create a new debate session.

    Args:
        request: CreateDebateSessionRequest with session details

    Returns:
        DebateSessionResponse with created session
    """
    # Ensure table exists
    await _create_session_table_if_not_exists()

    # Generate session ID
    session_id = str(uuid4())
    timestamp = now_timestamp()

    # Create session object
    session = DebateSession(
        session_id=session_id,
        topic_name=request.topic_name,
        creator_wallet=request.creator_wallet,
        creator_names=request.creator_names,
        participants=request.participants,
        created_at=timestamp,
        status="active",
        total_contributions=0,
    )

    # Insert into database
    await insert_session(session)

    logger.info(
        f"Debate session created: {session_id} - "
        f"Topic: '{request.topic_name}' - "
        f"Creator: {request.creator_wallet} - "
        f"Participants: {len(request.participants)}"
    )

    # Return response
    return DebateSessionResponse(
        session_id=session.session_id,
        topic_name=session.topic_name,
        creator_wallet=session.creator_wallet,
        creator_names=session.creator_names,
        participants=session.participants,
        created_at=session.created_at,
        status=session.status,
        message="Debate session created successfully"
    )
