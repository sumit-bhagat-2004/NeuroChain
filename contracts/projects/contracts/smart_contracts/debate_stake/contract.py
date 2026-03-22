from algopy import (
    ARC4Contract,
    Account,
    Global,
    GlobalState,
    BoxMap,
    Txn,
    UInt64,
    arc4,
    itxn,
    gtxn,
)


class DebateStake(ARC4Contract):

    def __init__(self) -> None:
        self.debate_id = GlobalState(arc4.String, key="debate_id")
        self.total_pool = GlobalState(UInt64, key="pool")
        self.is_settled = GlobalState(arc4.Bool, key="settled")
        self.winner_node_id = GlobalState(arc4.String, key="winner")
        self.owner = GlobalState(Account, key="owner")
        self.stakes = BoxMap(arc4.Address, UInt64, key_prefix="s_")
        self.stances = BoxMap(arc4.Address, arc4.String, key_prefix="t_")

    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def initialize(self, debate_id: arc4.String) -> None:
        self.debate_id.value = debate_id
        self.total_pool.value = UInt64(0)
        self.is_settled.value = arc4.Bool(False)
        self.winner_node_id.value = arc4.String("")
        self.owner.value = Txn.sender

    @arc4.abimethod
    def stake(self, stance_node_id: arc4.String) -> None:
        assert not self.is_settled.value, "Debate already settled"
        caller = arc4.Address(Txn.sender)
        assert caller not in self.stakes, "Already staked"
        pay = gtxn.PaymentTransaction(0)
        assert pay.receiver == Global.current_application_address, "Pay must go to contract"
        assert pay.amount > UInt64(0), "Must send ALGO to stake"
        self.stakes[caller] = pay.amount
        self.stances[caller] = stance_node_id
        self.total_pool.value = self.total_pool.value + pay.amount

    @arc4.abimethod
    def settle(self, winner_node_id: arc4.String) -> None:
        assert Txn.sender == self.owner.value, "Only owner can settle"
        assert not self.is_settled.value, "Already settled"
        self.is_settled.value = arc4.Bool(True)
        self.winner_node_id.value = winner_node_id

    @arc4.abimethod
    def claim(self) -> None:
        assert self.is_settled.value, "Not settled yet"
        caller = arc4.Address(Txn.sender)
        assert caller in self.stakes, "No stake found"
        assert caller in self.stances, "No stance found"
        caller_stance_bytes = self.stances[caller].bytes
        winner_bytes = self.winner_node_id.value.bytes
        assert caller_stance_bytes == winner_bytes, "You backed the wrong side"
        caller_stake = self.stakes[caller]
        assert caller_stake > UInt64(0), "Already claimed or zero stake"
        self.stakes[caller] = UInt64(0)
        itxn.Payment(
            receiver=Txn.sender,
            amount=caller_stake,
            fee=UInt64(0),
        ).submit()

    @arc4.abimethod(readonly=True)
    def get_pool_info(self) -> arc4.UInt64:
        return arc4.UInt64(self.total_pool.value)

    @arc4.abimethod(readonly=True)
    def get_winner(self) -> arc4.String:
        assert self.is_settled.value, "Not settled yet"
        return arc4.String.from_bytes(self.winner_node_id.value.bytes)
