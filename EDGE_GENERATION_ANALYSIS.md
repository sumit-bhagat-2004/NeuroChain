# Edge Generation Issue Analysis

## Problem Statement
Edges are not being generated when nodes are created in the `/nodes` endpoint, even though nodes have `primary_text` and `accumulated_text` fields.

## Root Causes Identified

### 1. First Node Has No Candidates
**Location**: `node_controller.py:140-144`
- When creating the very first node, `fetch_candidates_by_vector()` queries for candidates but finds NONE
- Query excludes current node: `WHERE id != %(exclude_id)s`
- Result: 0 edges created ✓ (expected behavior)

### 2. Subsequent Nodes May Not Meet Threshold
**Location**: `config.py:30`, `scoring_service.py:80-84`

**Current Settings**:
- `score_threshold: 0.7` (70%) - Very high!
- Scoring formula: `score = 0.6 × semantic + 0.2 × keyword + 0.2 × time`

**Example Math**:
- Perfect semantic similarity (1.0): `0.6 × 1.0 + 0.2 × kw + 0.2 × tm = 0.6 + 0.2(kw+tm)`
- For edge to be created: `0.6 + 0.2(kw+tm) ≥ 0.7`
- This requires: `(kw + tm) ≥ 0.5` (keyword overlap + time proximity)

**Problem**:
- If two nodes have similar embeddings (0.7 semantic) but different keywords: `0.6×0.7 + 0.2×0.1 + 0.2×1.0 = 0.42 + 0.02 + 0.2 = 0.64` ❌ (below threshold!)
- Threshold is TOO HIGH for semantic-only matches

### 3. Scoring Weights Favor Time Decay
**Location**: `scoring_service.py:15-17`

```python
SEMANTIC_WEIGHT = 0.6   # 60% - embedding similarity
KEYWORD_WEIGHT = 0.2    # 20% - word overlap
TIME_WEIGHT = 0.2       # 20% - recency (time decay)
```

**Issue**:
- Only 60% of score is based on actual content similarity
- 20% goes to keyword extraction (very strict - requires exact word matches)
- 20% goes to time decay (timestamps matter too much)
- For new nodes in same session, time gap might be small but not 1.0 perfect

### 4. Primary/Accumulated Text NOT Used in Vector Search
**Location**: `snowflake_service.py:255-268`

The vector similarity search ONLY uses the `embedding` field:
```sql
VECTOR_COSINE_SIMILARITY(
    embedding,
    PARSE_JSON(%(embedding_json)s)::VECTOR(FLOAT, 768)
) AS similarity
```

The `primary_text` and `accumulated_text` fields are **stored** but **NOT indexed** or used for similarity matching. They're only used for display.

## Diagnosis Flow

### When You Create Node #1
1. ✅ Embedding generated
2. ⚠️ Candidates query finds 0 results (no other nodes exist)
3. ✅ Returns 0 edges (expected)

### When You Create Node #2 (different topic)
1. ✅ Embedding generated
2. ✅ Candidates finds Node #1
3. ❌ Similarity score calculated: `0.5 × 0.6 + 0.1 × 0.2 + 1.0 × 0.2 = 0.3 + 0.02 + 0.2 = 0.52`
4. ❌ Score 0.52 < threshold 0.7 → **NO EDGE CREATED**

### When You Create Node #2 (similar topic)
1. ✅ Embedding generated
2. ✅ Candidates finds Node #1
3. ✅ Similarity score: `0.8 × 0.6 + 0.4 × 0.2 + 1.0 × 0.2 = 0.48 + 0.08 + 0.2 = 0.76`
4. ✅ Score 0.76 ≥ 0.7 → **EDGE CREATED** ✓

## Solutions

### Option 1: Lower the Score Threshold (Recommended for Testing)
**File**: `.env` or `config.py:30`
```python
score_threshold: float = 0.5  # Changed from 0.7
```

**Impact**:
- More edges created
- More connections visible in graph
- May create lower-quality edges

### Option 2: Rebalance Scoring Weights
**File**: `scoring_service.py:15-17`

Option A (Semantic-focused):
```python
SEMANTIC_WEIGHT = 0.8  # 80% - prioritize embedding similarity
KEYWORD_WEIGHT = 0.1   # 10%
TIME_WEIGHT = 0.1      # 10%
```

Option B (Balanced):
```python
SEMANTIC_WEIGHT = 0.7  # 70%
KEYWORD_WEIGHT = 0.15  # 15%
TIME_WEIGHT = 0.15     # 15%
```

### Option 3: Use Primary/Accumulated Text for Similarity
**File**: `snowflake_service.py:246-292`

Modify `_fetch_candidates_by_vector_sync()` to also compute semantic similarity on `accumulated_text`:
```sql
-- Add full-text search or re-rank by text similarity
SELECT ...
WHERE CONTAINS(accumulated_text, ?)  -- OR use ARRAY_CONTAINS on parsed keywords
```

### Option 4: Add Keyword Extraction Debugging
**File**: `utils/keywords.py`

The `keyword_score()` function uses Jaccard similarity. For unrelated topics, this will be 0. Add logging to see actual keyword overlap scores.

## Testing Recommendation

1. Create 3-4 nodes with **clearly related** topics
2. Check logs to see actual similarity scores
3. If scores are below 0.7, lower threshold to 0.5
4. Monitor edge creation in logs:
   - "Qualified candidates: X/20"
   - "Created X edges"

## Why primary_text and accumulated_text Don't Help

The fields are defined and stored but:
- ❌ Not included in vector similarity search
- ❌ Not full-text indexed
- ✅ Returned in API responses for display
- ✅ Used in debate analytics

To use them for edge generation, would need to:
1. Compute semantic embedding on `accumulated_text` (already done!)
2. Use that embedding for vector similarity (already done!)
3. The issue is the **threshold**, not the text fields

## Summary

**Primary Issue**: Score threshold of 0.7 is too high
**Secondary Issue**: Scoring weights give too much weight to keyword overlap (strict)
**The Fields Are Fine**: `primary_text` and `accumulated_text` are used (via embeddings)

**Quick Fix**: Lower `score_threshold` in `.env` to 0.5-0.6
