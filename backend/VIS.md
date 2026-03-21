# 🎤 Debate System - Visual Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DEBATE TRANSCRIPTION SYSTEM               │
└─────────────────────────────────────────────────────────────┘

INPUT
  ↓
┌──────────────────────┐
│  New Transcription   │
│  - Speaker: "A"      │
│  - Text: "..."       │
└──────────────────────┘
  ↓
┌──────────────────────┐
│ Generate Embedding   │
│ (Snowflake Arctic)   │
│ → 768-dim vector     │
└──────────────────────┘
  ↓
┌──────────────────────┐
│ Fetch All Existing   │
│ Debate Nodes         │
└──────────────────────┘
  ↓
┌──────────────────────┐
│ Calculate Similarity │
│ with Each Node       │
│ (Cosine Similarity)  │
└──────────────────────┘
  ↓
┌─────────────────────────────────────────┐
│        Find Best Match                  │
│  Best Score: 0.82  (Node #1)            │
│  Next Best: 0.35  (Node #2)             │
└─────────────────────────────────────────┘
  ↓
  ┌─────────────────────┐
  │ Similarity > 0.75?  │
  └─────────────────────┘
         ↙           ↘
      YES             NO
       ↓               ↓
  ┌──────────┐   ┌──────────┐
  │  MERGE   │   │  CREATE  │
  └──────────┘   └──────────┘
       ↓               ↓
  ┌─────────────────────────────┐
  │ Update Existing Node:       │
  │ • Append text               │
  │ • Update embedding          │
  │ • Add speaker               │
  │ • Record merge history      │
  │ • Increment merge count     │
  └─────────────────────────────┘
       ↓               ↓
  ┌─────────────────────────────┐
  │ Response                    │
  │ action: "merged"/"created"  │
  │ node_id: "uuid"             │
  │ similarity_score: 0.82      │
  └─────────────────────────────┘
```

## Data Evolution Example

### Scenario: 3 Transcriptions on AI Education

```
TIME: T0
═══════════════════════════════════════════════════
Input: "AI will transform education" (Speaker A)
Action: CREATE (no existing nodes)

[Node 1]
┌─────────────────────────────────────────────────┐
│ ID: node-001                                    │
│ Primary: "AI will transform education"          │
│ Accumulated: "AI will transform education"      │
│ Speakers: [A]                                   │
│ Merge Count: 0                                  │
│ History: []                                     │
└─────────────────────────────────────────────────┘


TIME: T1
═══════════════════════════════════════════════════
Input: "AI enables personalized learning" (Speaker B)
Similarity with Node 1: 0.82 ✅ > 0.75
Action: MERGE into Node 1

[Node 1] ← MERGED
┌─────────────────────────────────────────────────┐
│ ID: node-001                                    │
│ Primary: "AI will transform education"          │
│ Accumulated:                                    │
│   "AI will transform education"                 │
│   "[Speaker B]: AI enables personalized..."     │
│ Speakers: [A, B]                                │
│ Merge Count: 1                                  │
│ History: [                                      │
│   {merged_at: T1, similarity: 0.82, ...}        │
│ ]                                               │
└─────────────────────────────────────────────────┘


TIME: T2
═══════════════════════════════════════════════════
Input: "Renewable energy creates jobs" (Speaker A)
Similarity with Node 1: 0.35 ❌ < 0.75
Action: CREATE new node

[Node 1]                    [Node 2] ← NEW
┌──────────────────┐       ┌──────────────────┐
│ AI Education     │       │ Renewable Energy │
│ Speakers: [A,B]  │       │ Speakers: [A]    │
│ Merge Count: 1   │       │ Merge Count: 0   │
└──────────────────┘       └──────────────────┘
```

## Merge Decision Matrix

```
                    Similarity Score
                 Low              Medium            High
                0.0 ──────────────── 0.75 ──────────── 1.0
                 │                    │                │
Different   ────┤                    │                │
Topic           │     CREATE         │      MERGE     │
                │     NEW NODE       │      INTO      │
Similar     ────┤                    │      EXISTING  │
Topic           │                    │                │
                └────────────────────┴────────────────┘
                      THRESHOLD
```

## Merge History Timeline

```
Node 1: "AI in Education"

T0: Created by Speaker A
│
├─ T1: Merged from Speaker B (similarity: 0.82)
│   └─ "AI enables personalized learning"
│
├─ T2: Merged from Speaker C (similarity: 0.79)
│   └─ "AI tutoring helps students"
│
├─ T3: Merged from Speaker D (similarity: 0.76)
│   └─ "Adaptive learning systems improve outcomes"
│
└─ Current State: 3 merges, 4 speakers

Accumulated Text Length: 487 characters
```

## Comparison: Traditional vs Git Merge Flow

### Traditional Approach (No Merging)

```
Speaker A: "AI transforms education"
  → Node 1

Speaker B: "AI enables personalized learning"
  → Node 2  (duplicate!)

Speaker C: "AI tutoring helps students"
  → Node 3  (duplicate!)

Speaker D: "Adaptive learning improves outcomes"
  → Node 4  (duplicate!)

Result: 4 fragmented nodes
```

### Git Merge Flow (Smart Merging)

```
Speaker A: "AI transforms education"
  → Node 1

Speaker B: "AI enables personalized learning"
  → MERGE into Node 1 (similar!)

Speaker C: "AI tutoring helps students"
  → MERGE into Node 1 (similar!)

Speaker D: "Adaptive learning improves outcomes"
  → MERGE into Node 1 (similar!)

Result: 1 comprehensive node with full discussion
```

## Database Schema Visualization

```
debate_nodes Table
┌──────────────┬─────────────────┬─────────────────────────┐
│ id           │ primary_text    │ accumulated_text        │
├──────────────┼─────────────────┼─────────────────────────┤
│ node-001     │ "AI will..."    │ "AI will...             │
│              │                 │  [B]: AI enables...     │
│              │                 │  [C]: AI tutoring..."   │
└──────────────┴─────────────────┴─────────────────────────┘

┌──────────────┬─────────────┬──────────────────────────┐
│ created_at   │ merge_count │ speakers                 │
├──────────────┼─────────────┼──────────────────────────┤
│ 1710000000   │ 2           │ ["A", "B", "C"]          │
└──────────────┴─────────────┴──────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ merge_history (JSON)                                   │
├────────────────────────────────────────────────────────┤
│ [                                                      │
│   {                                                    │
│     merged_at: 1710000100,                             │
│     similarity_score: 0.82,                            │
│     merged_speaker: "B",                               │
│     merged_text: "AI enables..."                       │
│   },                                                   │
│   {                                                    │
│     merged_at: 1710000200,                             │
│     similarity_score: 0.79,                            │
│     merged_speaker: "C",                               │
│     merged_text: "AI tutoring..."                      │
│   }                                                    │
│ ]                                                      │
└────────────────────────────────────────────────────────┘
```

## API Response Flow

```
POST /debate/transcription
{
  "speaker": "Speaker B",
  "text": "AI enables personalized learning"
}
    ↓
    ↓ Processing...
    ↓
MERGED Response ✅
{
  "action": "merged",
  "node_id": "node-001",
  "similarity_score": 0.82,
  "merge_count": 1,
  "accumulated_length": 234
}

GET /debate/node/node-001
    ↓
    ↓ Fetching...
    ↓
Node Details ✅
{
  "id": "node-001",
  "primary_text": "AI will transform education",
  "accumulated_text": "...",
  "speakers": ["Speaker A", "Speaker B"],
  "merge_count": 1,
  "merge_history": [...]
}
```

## Testing Flow

```
┌─────────────────────────────────────────────────┐
│         RUN: ./test_debate.sh                   │
└─────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  1. Create first node         │
    │     ✅ action: "created"      │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  2. Add similar content       │
    │     ✅ action: "merged"       │
    │     ✅ similarity: 0.82       │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  3. Add another similar       │
    │     ✅ action: "merged"       │
    │     ✅ merge_count: 2         │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  4. Add different topic       │
    │     ✅ action: "created"      │
    │     ✅ new node_id            │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────┐
    │  5-7. Verify data             │
    │     ✅ merged content         │
    │     ✅ merge history          │
    │     ✅ statistics             │
    └───────────────────────────────┘
                    ↓
            ✅ ALL TESTS PASS
```

---

**Legend**:
- ✅ Success condition met
- ❌ Condition not met
- → Flow direction
- ├─ Branch/fork
- └─ End of branch