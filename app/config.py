from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""

    # AWS
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    dynamodb_table_prefix: str = "remit_"
    dynamodb_endpoint_url: str | None = None  # For local DynamoDB

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    # FX API
    fx_api_key: str = ""
    fx_api_base_url: str = "https://v6.exchangerate-api.com/v6"

    # CoinGecko
    coingecko_api_base_url: str = "https://api.coingecko.com/api/v3"

    # Wise
    wise_api_base_url: str = "https://api.sandbox.transferwise.tech"
    wise_api_token: str = ""  # Personal API token from sandbox settings

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    rate_check_interval_minutes: int = 15

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    def table_name(self, name: str) -> str:
        return f"{self.dynamodb_table_prefix}{name}"


settings = Settings()
