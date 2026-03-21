#!/usr/bin/env python3
"""
Fix script for debate_snowflake_service.py VECTOR type issue
Run this in your backend directory: python fix_debate_vector.py
"""

import re
import sys
from pathlib import Path

def fix_debate_snowflake_service():
    """Fix the VECTOR type conversion in debate_snowflake_service.py"""
    
    file_path = Path("app/services/debate_snowflake_service.py")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print("Make sure you run this from the backend/ directory")
        return False
    
    print(f"📝 Reading {file_path}...")
    content = file_path.read_text()
    
    # Fix 1: _insert_debate_node_sync
    old_insert = r'''@async_snowflake
def _insert_debate_node_sync\(node: DebateNode\) -> None:
    """Insert debate node into database\."""
    embedding_str = "\[" \+ ","\join\(str\(x\) for x in node\.embedding\) \+ "\]"
    merge_history_json = json\.dumps\(\[m\.model_dump\(\) for m in node\.merge_history\]\)
    speakers_json = json\.dumps\(node\.speakers\)

    sql = """
        INSERT INTO debate_nodes \(
            id, primary_text, accumulated_text, embedding,
            created_at, last_updated, merge_count,
            merge_history, speakers
        \)
        VALUES \(%s, %s, %s, %s, %s, %s, %s, %s, %s\)
    """

    _execute_non_query\(sql, \[
        node\.id,
        node\.primary_text,
        node\.accumulated_text,
        embedding_str,
        node\.created_at,
        node\.last_updated,
        node\.merge_count,
        merge_history_json,
        speakers_json,
    \]\)'''
    
    new_insert = '''@async_snowflake
def _insert_debate_node_sync(node: DebateNode) -> None:
    """Insert debate node into database."""
    # Convert embedding to JSON array string
    embedding_json = json.dumps(node.embedding)
    merge_history_json = json.dumps([m.model_dump() for m in node.merge_history])
    speakers_json = json.dumps(node.speakers)

    # Use TO_VECTOR(PARSE_JSON()) to properly convert to VECTOR type
    sql = """
        INSERT INTO debate_nodes (
            id, primary_text, accumulated_text, embedding,
            created_at, last_updated, merge_count,
            merge_history, speakers
        )
        VALUES (?, ?, ?, TO_VECTOR(PARSE_JSON(?), 768, 'FLOAT'), ?, ?, ?, ?, ?)
    """

    _execute_non_query(sql, [
        node.id,
        node.primary_text,
        node.accumulated_text,
        embedding_json,
        node.created_at,
        node.last_updated,
        node.merge_count,
        merge_history_json,
        speakers_json,
    ])'''
    
    # Fix 2: _update_debate_node_sync
    old_update = r'''@async_snowflake
def _update_debate_node_sync\(node: DebateNode\) -> None:
    """Update existing debate node\."""
    embedding_str = "\[" \+ ","\join\(str\(x\) for x in node\.embedding\) \+ "\]"
    merge_history_json = json\.dumps\(\[m\.model_dump\(\) for m in node\.merge_history\]\)
    speakers_json = json\.dumps\(node\.speakers\)

    sql = """
        UPDATE debate_nodes
        SET
            accumulated_text = %s,
            embedding = %s,
            last_updated = %s,
            merge_count = %s,
            merge_history = %s,
            speakers = %s
        WHERE id = %s
    """

    _execute_non_query\(sql, \[
        node\.accumulated_text,
        embedding_str,
        node\.last_updated,
        node\.merge_count,
        merge_history_json,
        speakers_json,
        node\.id,
    \]\)'''
    
    new_update = '''@async_snowflake
def _update_debate_node_sync(node: DebateNode) -> None:
    """Update existing debate node."""
    # Convert embedding to JSON array string
    embedding_json = json.dumps(node.embedding)
    merge_history_json = json.dumps([m.model_dump() for m in node.merge_history])
    speakers_json = json.dumps(node.speakers)

    # Use TO_VECTOR(PARSE_JSON()) to properly convert to VECTOR type
    sql = """
        UPDATE debate_nodes
        SET
            accumulated_text = ?,
            embedding = TO_VECTOR(PARSE_JSON(?), 768, 'FLOAT'),
            last_updated = ?,
            merge_count = ?,
            merge_history = ?,
            speakers = ?
        WHERE id = ?
    """

    _execute_non_query(sql, [
        node.accumulated_text,
        embedding_json,
        node.last_updated,
        node.merge_count,
        merge_history_json,
        speakers_json,
        node.id,
    ])'''
    
    # Apply fixes
    changes_made = 0
    
    if 'embedding_str = "[" + ","' in content:
        print("✅ Found old INSERT pattern, fixing...")
        # Simple string replacement for the insert function
        content = content.replace(
            'embedding_str = "[" + ",".join(str(x) for x in node.embedding) + "]"',
            '# Convert embedding to JSON array string\n    embedding_json = json.dumps(node.embedding)'
        )
        content = content.replace(
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
            'VALUES (?, ?, ?, TO_VECTOR(PARSE_JSON(?), 768, \'FLOAT\'), ?, ?, ?, ?, ?)'
        )
        content = content.replace(
            '        embedding_str,',
            '        embedding_json,'
        )
        changes_made += 1
    
    if 'UPDATE debate_nodes' in content and 'embedding = %s' in content:
        print("✅ Found old UPDATE pattern, fixing...")
        # Fix UPDATE statement
        content = content.replace(
            'embedding = %s,',
            'embedding = TO_VECTOR(PARSE_JSON(?), 768, \'FLOAT\'),'
        )
        content = content.replace(
            'WHERE id = %s',
            'WHERE id = ?'
        )
        # Replace SET placeholders
        content = content.replace(
            'accumulated_text = %s,',
            'accumulated_text = ?,'
        )
        content = content.replace(
            'last_updated = %s,',
            'last_updated = ?,'
        )
        content = content.replace(
            'merge_count = %s,',
            'merge_count = ?,'
        )
        content = content.replace(
            'merge_history = %s,',
            'merge_history = ?,'
        )
        content = content.replace(
            'speakers = %s',
            'speakers = ?'
        )
        changes_made += 1
    
    if changes_made > 0:
        print(f"💾 Writing fixes to {file_path}...")
        file_path.write_text(content)
        print(f"✅ Successfully fixed {changes_made} functions!")
        print("\n🔄 Please restart your server:")
        print("   uvicorn app.main:app --reload --port 8000")
        return True
    else:
        print("ℹ️  No changes needed - file appears already fixed")
        return True

if __name__ == "__main__":
    success = fix_debate_snowflake_service()
    sys.exit(0 if success else 1)