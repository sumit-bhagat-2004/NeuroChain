#!/usr/bin/env python
"""
NeuroChain - Contract Deployment Verification Test
Tests both LiveProof and DebateStake contracts on LocalNet
"""

import sys
import os
from pathlib import Path

# Add contracts to path
contracts_path = Path(__file__).parent / "contracts" / "projects" / "contracts"
sys.path.insert(0, str(contracts_path / "smart_contracts"))

from algokit_utils import AlgorandClient
from smart_contracts.artifacts.neurochain.live_proof_client import LiveProofFactory
from smart_contracts.artifacts.debate_stake.debate_stake_client import DebateStakeFactory

def test_contracts():
    """Test both deployed smart contracts"""

    # Initialize
    os.chdir(contracts_path)
    algorand = AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    results = {
        "liveproof": False,
        "debatestake": False,
        "errors": []
    }

    print("\n" + "="*70)
    print("  ✅ NEUROCHAIN DEPLOYMENT - CONTRACT VERIFICATION TEST")
    print("="*70)

    # Test LiveProof Contract
    print("\n📦 LiveProof Smart Contract (App ID 1002)")
    print("-"*70)
    try:
        lp_factory = LiveProofFactory(algorand, default_sender=deployer.address)
        lp_client = lp_factory.get_app_client_by_id(1002)
        print(f"  Address: {lp_client.app_address}")
        print(f"  Name:    {lp_client.app_name}")

        # Test method call
        composer = lp_client.new_group()
        composer.get_total_proofs()
        responses = composer.send()

        print(f"  Status:  ✅ OPERATIONAL")
        print(f"  Test:    get_total_proofs() ✓")
        results["liveproof"] = True
    except Exception as e:
        print(f"  Status:  ❌ FAILED")
        print(f"  Error:   {str(e)[:80]}")
        results["errors"].append(f"LiveProof: {str(e)}")

    # Test DebateStake Contract
    print("\n📦 DebateStake Smart Contract (App ID 1034)")
    print("-"*70)
    try:
        ds_factory = DebateStakeFactory(algorand, default_sender=deployer.address)
        ds_client = ds_factory.get_app_client_by_id(1034)
        print(f"  Address: {ds_client.app_address}")
        print(f"  Name:    {ds_client.app_name}")

        # Test method call
        composer = ds_client.new_group()
        composer.get_pool_info()
        responses = composer.send()

        print(f"  Status:  ✅ OPERATIONAL")
        print(f"  Test:    get_pool_info() ✓")
        results["debatestake"] = True
    except Exception as e:
        print(f"  Status:  ❌ FAILED")
        print(f"  Error:   {str(e)[:80]}")
        results["errors"].append(f"DebateStake: {str(e)}")

    # Summary
    print("\n" + "="*70)
    if results["liveproof"] and results["debatestake"]:
        print("  ✅ SUCCESS - ALL CONTRACTS VERIFIED AND OPERATIONAL!")
        print("="*70)
        print("\n📋 Deployment Summary:")
        print(f"   LiveProof App ID:   1002")
        print(f"   DebateStake App ID: 1034")
        print(f"   Network:            LocalNet")
        print(f"   Status:             ✅ READY FOR INTEGRATION")
        print("\n🚀 Next Steps:")
        print("   1. Start backend: cd backend && uvicorn app.main:app --reload")
        print("   2. Start frontend: cd frontend && npm run dev")
        print("   3. Test API endpoints: http://localhost:8000/docs")
        print("   4. View UI: http://localhost:3000")
        print("")
        return 0
    else:
        print("  ❌ FAILURE - SOME CONTRACTS NOT OPERATIONAL")
        print("="*70)
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")
        print("")
        return 1

if __name__ == "__main__":
    exit_code = test_contracts()
    sys.exit(exit_code)
