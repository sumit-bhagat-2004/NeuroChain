import os
import sys
import hashlib
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

CONTRACT_PATH = Path(__file__).parent.parent / "contracts/projects/contracts"
sys.path.insert(0, str(CONTRACT_PATH))

import algokit_utils
from algokit_utils import BoxReference
from smart_contracts.artifacts.neurochain.live_proof_client import (
    LiveProofClient,
    AnchorProofArgs,
    GetProofArgs,
    ProofExistsArgs,
)

app = FastAPI(title="LiveProof Blockchain API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_client() -> LiveProofClient:
    algorand = algokit_utils.AlgorandClient.from_environment()

    # Get the base64-encoded private key directly
    private_key_b64 = os.getenv("DEPLOYER_PRIVATE_KEY", "")

    if not private_key_b64:
        raise ValueError("DEPLOYER_PRIVATE_KEY environment variable is not set")

    # Pass to SigningAccount
    account = algokit_utils.SigningAccount(private_key=private_key_b64)

    return algorand.client.get_typed_app_client_by_id(
        LiveProofClient,
        app_id=int(os.getenv("APP_ID", 1002)),
        default_sender=account.address,
        default_signer=account.signer,
    )
# ── Models ────────────────────────────────────────────────────────────────────

class AnchorRequest(BaseModel):
    node_id: str
    text: str
    embedding: list[float]

class ProofResponse(BaseModel):
    node_id: str
    text_hash: str
    embedding_hash: str
    timestamp: int
    creator: str
    app_id: int

# ── Helpers ───────────────────────────────────────────────────────────────────

def hash_text(text: str, timestamp: int) -> str:
    return hashlib.sha256(f"{text}{timestamp}".encode()).hexdigest()

def hash_embedding(embedding: list[float]) -> str:
    return hashlib.sha256(
        json.dumps(embedding, separators=(",", ":")).encode()
    ).hexdigest()

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "app_id": int(os.getenv("APP_ID", 1002))}


@app.post("/anchor", response_model=ProofResponse)
def anchor_proof(req: AnchorRequest):
    """
    Called by the AI backend after creating a node.
    Anchors the proof on Algorand and returns the proof details.
    """
    client = get_client()
    timestamp = int(time.time())
    text_hash = hash_text(req.text, timestamp)
    embedding_hash = hash_embedding(req.embedding)
    app_id = int(os.getenv("APP_ID", 1002))

    try:
        client.send.anchor_proof(
            args=AnchorProofArgs(
                node_id=req.node_id,
                text_hash=text_hash,
                embedding_hash=embedding_hash,
                timestamp=timestamp,
            ),
            params=algokit_utils.CommonAppCallParams(
                box_references=[BoxReference(app_id, f"p_{req.node_id}".encode())],
            ),
        )
    except Exception as e:
        print(f"ERROR in anchor_proof: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    return ProofResponse(
        node_id=req.node_id,
        text_hash=text_hash,
        embedding_hash=embedding_hash,
        timestamp=timestamp,
        creator="verified",
        app_id=app_id,
    )


@app.get("/proof/{node_id}", response_model=ProofResponse)
def get_proof(node_id: str):
    """
    Frontend calls this when a user clicks a node to see its proof.
    """
    client = get_client()
    app_id = int(os.getenv("APP_ID", 1002))

    try:
        result = client.send.get_proof(
            args=GetProofArgs(node_id=node_id),
            params=algokit_utils.CommonAppCallParams(
                box_references=[BoxReference(app_id, f"p_{node_id}".encode())],
            ),
        )
        proof = result.abi_return
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Proof not found: {e}")

    return ProofResponse(
        node_id=proof.node_id,
        text_hash=proof.text_hash,
        embedding_hash=proof.embedding_hash,
        timestamp=int(proof.timestamp),
        creator=proof.creator,
        app_id=app_id,
    )


@app.get("/exists/{node_id}")
def proof_exists(node_id: str):
    client = get_client()
    app_id = int(os.getenv("APP_ID", 1002))
    try:
        result = client.send.proof_exists(
            args=ProofExistsArgs(node_id=node_id),
            params=algokit_utils.CommonAppCallParams(
                box_references=[BoxReference(app_id, f"p_{node_id}".encode())],
            ),
        )
        return {"node_id": node_id, "exists": result.abi_return}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/stats")
def stats():
    client = get_client()
    try:
        result = client.send.get_total_proofs(args=None)
        return {"total_proofs": int(result.abi_return), "app_id": int(os.getenv("APP_ID", 1002))}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
