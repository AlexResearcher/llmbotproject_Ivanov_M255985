from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = Field(default="auth-service", alias="APP_NAME")
    env: str = Field(default="local", alias="ENV")
    jwt_secret: str = Field(default="change_me_super_secret", alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    sqlite_path: str = Field(default="./auth.db", alias="SQLITE_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    @property
    def resolved_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        return f"sqlite+aiosqlite:///{self.sqlite_path}"


settings = Settings()
