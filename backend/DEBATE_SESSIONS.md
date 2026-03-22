# Debate Session Management

Create and manage debate sessions with creators and participants tracking.

## Overview

The debate session management system allows you to:
- **Create debate sessions** with topics, creators, and participants
- **Track session metadata** - Creator wallets, participant info, timestamps
- **Link transcriptions to sessions** - Use session_id when adding transcriptions
- **Query sessions** - Get all sessions or specific session details

---

## API Endpoints

### 1. Create Debate Session

**POST** `/debate/creator`

Create a new debate session. The session ID is **auto-generated as UUID** in the backend.

**Request Body:**
```json
{
  "topic_name": "AI Ethics in Healthcare",
  "creator_wallet": "0x1234567890abcdef",
  "creator_names": ["Alice", "Bob"],
  "participants": [
    {
      "name": "Charlie",
      "wallet_address": "0x5678901234abcdef"
    },
    {
      "wallet_address": "0x9abcdef01234567"
    },
    {
      "name": "Eve",
      "wallet_address": "0xdef0123456789abc"
    }
  ]
}
```

**Note:** The `name` field for participants is **optional** since this is a Web3 application where wallet addresses serve as primary identifiers.

**Response:**
```json
{
  "session_id": "a7f3e2d1-4c5b-6a7e-8f9d-0c1b2a3d4e5f",
  "topic_name": "AI Ethics in Healthcare",
  "creator_wallet": "0x1234567890abcdef",
  "creator_names": ["Alice", "Bob"],
  "participants": [
    {
      "name": "Charlie",
      "wallet_address": "0x5678901234abcdef"
    },
    {
      "name": "Diana",
      "wallet_address": "0x9abcdef01234567"
    },
    {
      "name": "Eve",
      "wallet_address": "0xdef0123456789abc"
    }
  ],
  "created_at": 1711234567890,
  "status": "active",
  "message": "Debate session created successfully"
}
```

**Status Codes:**
- `201 Created` - Session created successfully
- `400 Bad Request` - Validation failed
- `500 Internal Server Error` - Server error

---

### 2. Get Session by ID

**GET** `/debate/session/{session_id}`

Retrieve details of a specific debate session.

**Example:**
```bash
GET /debate/session/a7f3e2d1-4c5b-6a7e-8f9d-0c1b2a3d4e5f
```

**Response:**
```json
{
  "session_id": "a7f3e2d1-4c5b-6a7e-8f9d-0c1b2a3d4e5f",
  "topic_name": "AI Ethics in Healthcare",
  "creator_wallet": "0x1234567890abcdef",
  "creator_names": ["Alice", "Bob"],
  "participants": [
    {
      "name": "Charlie",
      "wallet_address": "0x5678901234abcdef"
    },
    {
      "name": "Diana",
      "wallet_address": "0x9abcdef01234567"
    }
  ],
  "created_at": 1711234567890,
  "status": "active"
}
```

**Status Codes:**
- `200 OK` - Session found
- `404 Not Found` - Session doesn't exist
- `500 Internal Server Error` - Server error

---

### 3. Get All Sessions

**GET** `/debate/sessions`

Retrieve all debate sessions.

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "a7f3e2d1-4c5b-6a7e-8f9d-0c1b2a3d4e5f",
      "topic_name": "AI Ethics in Healthcare",
      "creator_wallet": "0x1234567890abcdef",
      "creator_names": ["Alice", "Bob"],
      "participants": [
        {
          "name": "Charlie",
          "wallet_address": "0x5678901234abcdef"
        }
      ],
      "created_at": 1711234567890,
      "status": "active",
      "total_contributions": 15
    },
    {
      "session_id": "b8g4f3e2-5d6c-7b8f-9g0e-1d2c3b4e5f6a",
      "topic_name": "Climate Change Policy",
      "creator_wallet": "0xabcdef0123456789",
      "creator_names": ["Frank"],
      "participants": [
        {
          "name": "Grace",
          "wallet_address": "0x123456789abcdef0"
        }
      ],
      "created_at": 1711234987654,
      "status": "active",
      "total_contributions": 8
    }
  ],
  "total": 2
}
```

---

## Linking Transcriptions to Sessions

Once you create a session, you can link transcriptions to it using the `debate_id` field:

**Example:**
```bash
POST /debate/transcription
{
  "speaker": "Charlie",
  "text": "I believe AI in healthcare requires strict privacy safeguards",
  "debate_id": "a7f3e2d1-4c5b-6a7e-8f9d-0c1b2a3d4e5f"
}
```

This links the transcription to the debate session, enabling session-filtered analytics in the future.

---

## Data Model

### DebateSession

```python
{
  "session_id": str,          # UUID generated in backend
  "topic_name": str,          # Debate topic
  "creator_wallet": str,      # Creator's wallet address
  "creator_names": [str],     # List of creator names
  "participants": [           # List of participants
    {
      "name": str,
      "wallet_address": str
    }
  ],
  "created_at": int,          # Timestamp (ms)
  "status": str,              # "active" or "closed"
  "total_contributions": int  # Number of transcriptions in session
}
```

---

## Database Schema

The `debate_sessions` table is automatically created on first use:

```sql
CREATE TABLE debate_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    topic_name VARCHAR(500) NOT NULL,
    creator_wallet VARCHAR(200) NOT NULL,
    creator_names VARIANT NOT NULL,        -- JSON array
    participants VARIANT NOT NULL,         -- JSON array of objects
    created_at BIGINT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    total_contributions INT DEFAULT 0
);
```

---

## Workflow Example

### 1. Create Session
```bash
POST /debate/creator
{
  "topic_name": "Web3 Governance Models",
  "creator_wallet": "0xCreatorWallet123",
  "creator_names": ["Alice"],
  "participants": [
    {"name": "Bob", "wallet_address": "0xBobWallet456"},
    {"name": "Carol", "wallet_address": "0xCarolWallet789"}
  ]
}

# Response includes session_id
{
  "session_id": "uuid-1234-5678",
  ...
}
```

### 2. Add Transcriptions to Session
```bash
POST /debate/transcription
{
  "speaker": "Bob",
  "text": "Quadratic voting could improve DAO governance",
  "debate_id": "uuid-1234-5678"
}

POST /debate/transcription
{
  "speaker": "Carol",
  "text": "We should also consider conviction voting mechanisms",
  "debate_id": "uuid-1234-5678"
}
```

### 3. Query Session
```bash
GET /debate/session/uuid-1234-5678

# Returns session details with total_contributions count
```

### 4. Generate Analytics (Future)
```bash
GET /debate/ai-analysis?session_id=uuid-1234-5678

# Filters analysis to only this session's discussions
```

---

## Validation Rules

### topic_name
- Required
- Must be non-empty string
- Max length: 500 characters

### creator_wallet
- Required
- Must be non-empty string
- Typically a blockchain address

### creator_names
- Required
- Must have at least 1 name
- Each name is a string

### participants
- Required
- Must have at least 1 participant
- Each participant must have:
  - `wallet_address`: string (required)
  - `name`: string (optional - Web3 wallet is the primary identifier)

---

## Future Enhancements

1. **Session Status Management**: Add endpoint to close/reopen sessions
2. **Participant Management**: Add/remove participants after session creation
3. **Session-Filtered Analytics**: Filter all analytics endpoints by session_id
4. **Session Permissions**: Track who can contribute to which sessions
5. **Session Templates**: Create reusable debate templates
6. **Session Invitations**: Send invites to participants via wallet addresses

---

## Testing

```bash
# 1. Create a session (with optional participant names)
curl -X POST http://localhost:8000/debate/creator \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "Test Debate",
    "creator_wallet": "0xtest123",
    "creator_names": ["Tester"],
    "participants": [
      {"wallet_address": "0xpart1"},
      {"name": "Participant2", "wallet_address": "0xpart2"}
    ]
  }'

# 2. Get the session (use session_id from response)
curl http://localhost:8000/debate/session/{session_id}

# 3. List all sessions
curl http://localhost:8000/debate/sessions

# 4. Add transcription to session
curl -X POST http://localhost:8000/debate/transcription \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "Participant1",
    "text": "My argument here...",
    "debate_id": "{session_id}"
  }'
```

---

## Summary

✅ **Session creation** with auto-generated UUID
✅ **Creator tracking** with wallet and names
✅ **Participant management** with names and wallets
✅ **Status tracking** - Active/closed sessions
✅ **Contribution counting** - Track # of transcriptions
✅ **REST API** - Full CRUD operations
✅ **Snowflake storage** - Persistent database
✅ **JSON serialization** - Arrays stored as VARIANT

The debate session system provides complete session lifecycle management for organizing debates!
