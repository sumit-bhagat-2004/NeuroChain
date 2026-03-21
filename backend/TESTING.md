# 🎤 Debate Transcription System - Testing Guide

## Overview

The debate transcription system implements a **"git merge flow"** for handling similar content. When a new transcription is added:

- **If similar to existing node** (similarity > 0.75): **MERGE** with existing node
- **If different from all nodes**: **CREATE** new node

This prevents duplicate nodes for similar debate topics and creates a consolidated view of the discussion.

## Quick Start Testing

### 1. Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 2. Verify Debate Endpoints

```bash
# Check health
curl http://localhost:8000/health

# Should see debate feature in response
```

## Test Scenarios

### Scenario 1: First Transcription (CREATE)

**Objective**: Create the first debate node

```bash
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker A",
    "text": "I believe that artificial intelligence will fundamentally transform the education system by providing personalized learning experiences for every student."
  }'
```

**Expected Response**:
```json
{
  "action": "created",
  "node_id": "550e8400-e29b-41d4-a716-446655440000",
  "similarity_score": null,
  "merge_count": 0,
  "accumulated_length": 163
}
```

**Verify**: `action` should be `"created"`

---

### Scenario 2: Similar Content (MERGE)

**Objective**: Add similar content - should merge with existing node

```bash
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker B",
    "text": "Building on that point, AI-powered education platforms can adapt to individual student needs, creating customized learning paths for each learner."
  }'
```

**Expected Response**:
```json
{
  "action": "merged",
  "node_id": "550e8400-e29b-41d4-a716-446655440000",  // Same ID as before!
  "similarity_score": 0.82,
  "merge_count": 1,
  "accumulated_length": 320
}
```

**Verify**:
- ✅ `action` should be `"merged"`
- ✅ `node_id` should match the previous node
- ✅ `similarity_score` should be > 0.75
- ✅ `merge_count` should be 1

---

### Scenario 3: Another Similar Statement (MERGE AGAIN)

**Objective**: Merge a third similar transcription

```bash
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker C",
    "text": "Personalized AI tutoring systems can identify knowledge gaps and provide targeted support to help students master difficult concepts."
  }'
```

**Expected Response**:
```json
{
  "action": "merged",
  "node_id": "550e8400-e29b-41d4-a716-446655440000",  // Same ID again!
  "similarity_score": 0.79,
  "merge_count": 2,
  "accumulated_length": 475
}
```

**Verify**:
- ✅ `merge_count` should now be 2
- ✅ Node is accumulating content

---

### Scenario 4: Different Topic (CREATE NEW NODE)

**Objective**: Add completely different topic - should create new node

```bash
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker A",
    "text": "The economic impact of renewable energy adoption includes job creation in solar panel manufacturing and wind turbine installation."
  }'
```

**Expected Response**:
```json
{
  "action": "created",
  "node_id": "660e8400-e29b-41d4-a716-446655440001",  // NEW ID!
  "similarity_score": null,
  "merge_count": 0,
  "accumulated_length": 142
}
```

**Verify**:
- ✅ `action` should be `"created"`
- ✅ `node_id` should be **different** from previous
- ✅ New node created because similarity < 0.75

---

### Scenario 5: View Accumulated Node

**Objective**: See the full merged content

```bash
# Get the first node ID from Scenario 1
NODE_ID="550e8400-e29b-41d4-a716-446655440000"

curl http://localhost:8000/debate/node/$NODE_ID
```

**Expected Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "primary_text": "I believe that artificial intelligence will...",
  "accumulated_text": "I believe that artificial intelligence will...\n\n[Speaker B]: Building on that point...\n\n[Speaker C]: Personalized AI tutoring systems...",
  "created_at": 1710000000000,
  "last_updated": 1710000300000,
  "merge_count": 2,
  "speakers": ["Speaker A", "Speaker B", "Speaker C"],
  "merge_history": [
    {
      "merged_at": 1710000100000,
      "similarity_score": 0.82,
      "merged_speaker": "Speaker B",
      "merged_text": "Building on that point..."
    },
    {
      "merged_at": 1710000300000,
      "similarity_score": 0.79,
      "merged_speaker": "Speaker C",
      "merged_text": "Personalized AI tutoring systems..."
    }
  ]
}
```

**Verify**:
- ✅ `accumulated_text` contains all merged content
- ✅ `merge_history` shows each merge with timestamp and similarity
- ✅ `speakers` array lists all contributors

---

### Scenario 6: View All Nodes

**Objective**: Get overview of all debate nodes

```bash
curl http://localhost:8000/debate/nodes
```

**Expected Response**:
```json
{
  "nodes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "primary_text": "I believe that artificial intelligence...",
      "accumulated_text": "...",
      "created_at": 1710000000000,
      "last_updated": 1710000300000,
      "merge_count": 2,
      "speakers": ["Speaker A", "Speaker B", "Speaker C"],
      "merge_history": [...]
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "primary_text": "The economic impact of renewable energy...",
      "accumulated_text": "...",
      "created_at": 1710000400000,
      "last_updated": 1710000400000,
      "merge_count": 0,
      "speakers": ["Speaker A"],
      "merge_history": []
    }
  ],
  "total": 2
}
```

**Verify**:
- ✅ Should see 2 nodes (AI education + renewable energy)
- ✅ First node has merges, second doesn't

---

### Scenario 7: Get Statistics

**Objective**: View debate statistics

```bash
curl http://localhost:8000/debate/stats
```

**Expected Response**:
```json
{
  "total_nodes": 2,
  "total_merges": 2,
  "unique_speakers": 3,
  "speakers": ["Speaker A", "Speaker B", "Speaker C"],
  "avg_merges_per_node": 1.0
}
```

---

## Complete Test Script

Save this as `test_debate.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
echo "🎤 Testing Debate Transcription System"
echo "======================================"

echo ""
echo "1️⃣ Adding first transcription (CREATE)..."
RESP1=$(curl -s -X POST "$BASE_URL/debate/transcription" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker A",
    "text": "I believe that artificial intelligence will fundamentally transform the education system by providing personalized learning experiences for every student."
  }')
echo "$RESP1" | python3 -m json.tool
NODE1_ID=$(echo "$RESP1" | python3 -c "import sys, json; print(json.load(sys.stdin)['node_id'])")
echo "Node ID: $NODE1_ID"

sleep 1

echo ""
echo "2️⃣ Adding similar content (should MERGE)..."
RESP2=$(curl -s -X POST "$BASE_URL/debate/transcription" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker B",
    "text": "Building on that point, AI-powered education platforms can adapt to individual student needs, creating customized learning paths for each learner."
  }')
echo "$RESP2" | python3 -m json.tool
ACTION2=$(echo "$RESP2" | python3 -c "import sys, json; print(json.load(sys.stdin)['action'])")
if [ "$ACTION2" = "merged" ]; then
  echo "✅ MERGED successfully!"
else
  echo "❌ Expected MERGE, got $ACTION2"
fi

sleep 1

echo ""
echo "3️⃣ Adding another similar statement (should MERGE again)..."
RESP3=$(curl -s -X POST "$BASE_URL/debate/transcription" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker C",
    "text": "Personalized AI tutoring systems can identify knowledge gaps and provide targeted support to help students master difficult concepts."
  }')
echo "$RESP3" | python3 -m json.tool
MERGE_COUNT=$(echo "$RESP3" | python3 -c "import sys, json; print(json.load(sys.stdin)['merge_count'])")
echo "Merge count: $MERGE_COUNT"

sleep 1

echo ""
echo "4️⃣ Adding different topic (should CREATE new node)..."
RESP4=$(curl -s -X POST "$BASE_URL/debate/transcription" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Speaker A",
    "text": "The economic impact of renewable energy adoption includes job creation in solar panel manufacturing and wind turbine installation."
  }')
echo "$RESP4" | python3 -m json.tool
ACTION4=$(echo "$RESP4" | python3 -c "import sys, json; print(json.load(sys.stdin)['action'])")
if [ "$ACTION4" = "created" ]; then
  echo "✅ Created new node successfully!"
else
  echo "❌ Expected CREATE, got $ACTION4"
fi

sleep 1

echo ""
echo "5️⃣ Viewing accumulated node..."
curl -s "$BASE_URL/debate/node/$NODE1_ID" | python3 -m json.tool

echo ""
echo "6️⃣ Getting all nodes..."
curl -s "$BASE_URL/debate/nodes" | python3 -m json.tool

echo ""
echo "7️⃣ Getting statistics..."
curl -s "$BASE_URL/debate/stats" | python3 -m json.tool

echo ""
echo "======================================"
echo "✅ Test complete!"
```

Make executable and run:
```bash
chmod +x test_debate.sh
./test_debate.sh
```

---

## Python Test Script

For more control, use Python:

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def add_transcription(speaker, text):
    """Add a transcription and print response."""
    print(f"\n➡️ {speaker}: {text[:50]}...")
    
    response = requests.post(
        f"{BASE_URL}/debate/transcription",
        json={"speaker": speaker, "text": text}
    )
    
    data = response.json()
    print(f"   Action: {data['action']}")
    print(f"   Node ID: {data['node_id']}")
    
    if data['action'] == 'merged':
        print(f"   Similarity: {data['similarity_score']:.3f}")
        print(f"   Merge count: {data['merge_count']}")
    
    return data

# Test sequence
print("🎤 Debate Transcription Test")
print("=" * 50)

# 1. First transcription (CREATE)
r1 = add_transcription(
    "Speaker A",
    "I believe that artificial intelligence will fundamentally transform the education system."
)
node1_id = r1['node_id']
time.sleep(0.5)

# 2. Similar content (MERGE)
r2 = add_transcription(
    "Speaker B",
    "AI-powered education platforms can adapt to individual student needs and create personalized learning paths."
)
time.sleep(0.5)

# 3. Another similar (MERGE)
r3 = add_transcription(
    "Speaker C",
    "Personalized AI tutoring identifies knowledge gaps and provides targeted support."
)
time.sleep(0.5)

# 4. Different topic (CREATE)
r4 = add_transcription(
    "Speaker A",
    "Renewable energy adoption creates jobs in solar panel manufacturing."
)

# 5. View merged node
print(f"\n📊 Viewing merged node {node1_id}...")
response = requests.get(f"{BASE_URL}/debate/node/{node1_id}")
data = response.json()
print(f"   Speakers: {data['speakers']}")
print(f"   Merge count: {data['merge_count']}")
print(f"   Accumulated length: {len(data['accumulated_text'])} chars")

# 6. Stats
print("\n📈 Statistics:")
response = requests.get(f"{BASE_URL}/debate/stats")
stats = response.json()
print(json.dumps(stats, indent=2))

print("\n✅ Test complete!")
```

---

## Expected Behavior Summary

| Scenario | Input Similarity | Expected Action | Node Count |
|----------|-----------------|-----------------|------------|
| First transcription | N/A | CREATE | 1 |
| Similar content (>0.75) | High | MERGE | 1 |
| Another similar | High | MERGE | 1 |
| Different topic (<0.75) | Low | CREATE | 2 |

---

## Troubleshooting

**Merging when you expect new node**:
- Similarity threshold might be too low
- Try more different content

**Creating when you expect merge**:
- Content might not be similar enough
- Check `similarity_score` in response
- Threshold is 0.75 (can be adjusted in code)

**No response**:
- Check if server is running: `curl http://localhost:8000/health`
- Check Snowflake connection
- Review server logs

---

## Integration with Frontend

To integrate with your frontend, you can:

1. **Display debate nodes as clustered concepts**
2. **Show merge history timeline**
3. **Visualize speaker contributions**
4. **Highlight merged vs original nodes**

Example API call from JavaScript:

```javascript
// Add transcription
const response = await fetch('http://localhost:8000/debate/transcription', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    speaker: 'Speaker A',
    text: 'Your transcription text here...'
  })
});

const data = await response.json();

if (data.action === 'merged') {
  console.log(`Merged with node ${data.node_id}`);
  console.log(`Similarity: ${data.similarity_score}`);
} else {
  console.log(`Created new node ${data.node_id}`);
}
```

---

## Next Steps

1. ✅ Test with the provided scripts
2. ✅ Verify merge behavior
3. ✅ Check accumulated text format
4. ✅ Review merge history
5. 🔄 Integrate with your frontend
6. 🔄 Adjust similarity threshold if needed
7. 🔄 Add debate session tracking

**Threshold Tuning**:
- Edit `MERGE_SIMILARITY_THRESHOLD` in `app/services/debate_service.py`
- Lower (e.g., 0.65): More aggressive merging
- Higher (e.g., 0.85): More conservative, fewer merges