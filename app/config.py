from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Systems Lab"
    app_env: str = Field(default="dev")

    meta_access_token: str = Field(default="", description="Long-lived Meta Graph API token")
    ig_user_id: str = Field(default="")
    fb_page_id: str = Field(default="")

    publish_timeout_s: int = 15
    engagement_daily_limit: int = 20
    engagement_min_delay_s: float = 2.0
    engagement_max_delay_s: float = 6.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
