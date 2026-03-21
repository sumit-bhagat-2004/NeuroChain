# 🎤 Debate System - Quick Reference Card

## Installation (1 minute)

```bash
cd backend
pip install fastapi uvicorn snowflake-connector-python pydantic-settings numpy python-dotenv
cp .env.example .env
# Edit .env with Snowflake credentials
uvicorn app.main:app --reload --port 8000
```

## Core Concept

**Similarity > 0.75** → **MERGE** (extend existing node)  
**Similarity ≤ 0.75** → **CREATE** (new node)

## Quick Test

```bash
# Test 1: Create first node
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{"speaker":"A","text":"AI transforms education"}'

# Test 2: Merge similar content
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{"speaker":"B","text":"AI enables personalized learning"}'

# Test 3: Create different node
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{"speaker":"A","text":"Renewable energy creates jobs"}'
```

## Expected Results

| Test | Similarity | Action | Node Count |
|------|-----------|--------|------------|
| 1 | N/A | CREATE | 1 |
| 2 | ~0.82 | MERGE | 1 |
| 3 | ~0.35 | CREATE | 2 |

## API Cheat Sheet

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/debate/transcription` | POST | Add transcription |
| `/debate/node/{id}` | GET | Get node details |
| `/debate/nodes` | GET | List all nodes |
| `/debate/stats` | GET | Get statistics |

## Response Fields

**action**: `"merged"` or `"created"`  
**node_id**: UUID of node  
**similarity_score**: Float (only if merged)  
**merge_count**: Total merges for this node  
**accumulated_length**: Total text length

## Configuration

File: `app/services/debate_service.py`

```python
MERGE_SIMILARITY_THRESHOLD = 0.75  # Default

# Tuning guide:
# 0.65 = aggressive merging
# 0.75 = balanced (recommended)
# 0.85 = conservative
```

## Verification Checklist

- [ ] Server starts without errors
- [ ] First transcription creates node
- [ ] Similar transcription merges
- [ ] Different transcription creates new node
- [ ] `/debate/stats` shows correct counts
- [ ] Merge history visible in node details

## Troubleshooting

**"No merges happening"**  
→ Check similarity scores in response  
→ Lower threshold to 0.65

**"Too many merges"**  
→ Raise threshold to 0.85

**"Server won't start"**  
→ Check Snowflake credentials in `.env`  
→ Verify all dependencies installed

## Files Modified

New:
- `app/models/debate.py`
- `app/services/debate_service.py`
- `app/services/debate_snowflake_service.py`
- `app/controllers/debate_controller.py`
- `app/routes/debate.py`

Updated:
- `app/main.py` (added debate router)

## Database

Table: `debate_nodes`

Key columns:
- `accumulated_text` - All merged content
- `merge_count` - Number of merges
- `merge_history` - JSON array of merge records
- `speakers` - JSON array of contributors

## Performance

- Generate embedding: ~300ms
- Check similarity: ~10ms per node
- Total: ~500ms (100 nodes)

## Next Steps

1. ✅ Copy to GitHub repo
2. ✅ Run test script
3. ✅ Verify merge behavior
4. ⏭️ Adjust threshold
5. ⏭️ Frontend integration

---

**Need Help?**  
See `TESTING.md` for detailed test scenarios  
See `README.md` for full documentation  
See `IMPLEMENTATION_SUMMARY.md` for design decisions