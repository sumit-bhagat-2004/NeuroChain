import logging
import algokit_utils

logger = logging.getLogger(__name__)


def deploy() -> None:
    from smart_contracts.artifacts.debate_stake.debate_stake_client import (
        DebateStakeFactory,
        DebateStakeMethodCallCreateParams,
        InitializeArgs,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        DebateStakeFactory, default_sender=deployer.address
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
        create_params=DebateStakeMethodCallCreateParams(
            args=InitializeArgs(debate_id="default"),
            method="initialize(string)void",
        ),
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer.address,
                receiver=app_client.app_address,
            )
        )
        logger.info(
            f"✅ Deployed DebateStake — app_id={app_client.app_id} "
            f"app_address={app_client.app_address}"
        )
    else:
        logger.info(
            f"ℹ️  DebateStake already deployed — app_id={app_client.app_id}"
        )
