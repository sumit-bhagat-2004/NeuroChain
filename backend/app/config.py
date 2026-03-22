"""
Configuration — Pydantic Settings for environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Engine configuration loaded from environment variables."""

    # Snowflake connection
    snowflake_account: str
    snowflake_username: str
    snowflake_password: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_warehouse: str

    # Server
    port: int = 3000

     # Algorand / Blockchain
    live_proof_app_id: int = 1002
    debate_stake_app_id: int = 1034
    deployer_address: str = "NMNRVAW7ZYZAKXFFSTTLHHNDXLG742E36OSJMEW524XXXQTZO3R6HGOQT4"
    deployer_mnemonic: str = ""
    algod_server: str = "http://localhost"
    algod_port: int = 4001
    algod_token: str = "a" * 64

    # Engine parameters
    score_threshold: float = 0.7
    max_edges_per_node: int = 3
    time_decay_halflife: int = 86400000  # 24 hours in milliseconds
    candidate_limit: int = 20
    embedding_cache_capacity: int = 500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
