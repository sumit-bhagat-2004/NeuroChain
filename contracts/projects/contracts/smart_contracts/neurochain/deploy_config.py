import logging
import algokit_utils

logger = logging.getLogger(__name__)


def deploy() -> None:
    from smart_contracts.artifacts.neurochain.live_proof_client import (
        LiveProofFactory,
        LiveProofMethodCallCreateParams,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        LiveProofFactory, default_sender=deployer.address
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        create_params=LiveProofMethodCallCreateParams(
            args=None,
            method="initialize()void",
        ),
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        # Fund contract to cover box storage MBR costs
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=2),
                sender=deployer.address,
                receiver=app_client.app_address,
            )
        )

        logger.info(
            f"✅ Deployed LiveProof — app_id={app_client.app_id} "
            f"app_address={app_client.app_address}"
        )
    else:
        logger.info(
            f"ℹ️  LiveProof already deployed — app_id={app_client.app_id}"
        )
