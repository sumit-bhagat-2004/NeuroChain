from algopy import (
    ARC4Contract,
    Account,
    BoxMap,
    GlobalState,
    Txn,
    UInt64,
    arc4,
)


class ProofRecord(arc4.Struct):
    node_id: arc4.String
    text_hash: arc4.String
    embedding_hash: arc4.String
    timestamp: arc4.UInt64
    creator: arc4.Address


class LiveProof(ARC4Contract):
    """
    LiveProof — on-chain knowledge proof anchoring.
    Stores cryptographic fingerprints of ideas and their
    AI semantic embeddings. Each proof is queryable by node_id.
    """

    def __init__(self) -> None:
        self.proofs = BoxMap(arc4.String, ProofRecord, key_prefix="p_")
        self.total_proofs = GlobalState(UInt64, key="total")
        self.owner = GlobalState(Account, key="owner")

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def initialize(self) -> None:
        """Deploy contract. Called once by creator."""
        self.total_proofs.value = UInt64(0)
        self.owner.value = Txn.sender

    @arc4.abimethod
    def anchor_proof(
        self,
        node_id: arc4.String,
        text_hash: arc4.String,
        embedding_hash: arc4.String,
        timestamp: arc4.UInt64,
    ) -> None:
        """
        Anchor a knowledge node proof on-chain.
        Anyone can anchor — the caller's address is recorded as creator.
        node_id must be unique.
        """
        assert node_id not in self.proofs, "Proof already anchored for this node"
        assert arc4.String("") != text_hash, "text_hash cannot be empty"
        assert arc4.String("") != embedding_hash, "embedding_hash cannot be empty"

        self.proofs[node_id] = ProofRecord(
            node_id=node_id,
            text_hash=text_hash,
            embedding_hash=embedding_hash,
            timestamp=timestamp,
            creator=arc4.Address(Txn.sender),
        )

        self.total_proofs.value += UInt64(1)

    @arc4.abimethod(readonly=True)
    def get_proof(self, node_id: arc4.String) -> ProofRecord:
        """
        Fetch a proof record by node_id.
        Frontend calls this to display verification details.
        """
        assert node_id in self.proofs, "Proof not found"
        return self.proofs[node_id].copy()

    @arc4.abimethod(readonly=True)
    def proof_exists(self, node_id: arc4.String) -> arc4.Bool:
        """Check if a proof exists without fetching the full record."""
        return arc4.Bool(node_id in self.proofs)

    @arc4.abimethod(readonly=True)
    def get_total_proofs(self) -> arc4.UInt64:
        """Return total number of proofs anchored."""
        return arc4.UInt64(self.total_proofs.value)
