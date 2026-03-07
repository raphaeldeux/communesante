from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://communesante:password@db:5432/communesante"
    api_secret_token: str = "change_me"
    commune_insee: str = "44196"
    dgfip_api_key: str = ""
    sync_cron: str = "0 3 * * 0"
    log_level: str = "INFO"
    uploads_dir: str = "/app/uploads"

    class Config:
        env_file = ".env"


settings = Settings()
