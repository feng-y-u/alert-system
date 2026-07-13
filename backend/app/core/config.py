from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "校园账号异常登录监测平台"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "mysql+pymysql://campus_user:campus123@localhost:3306/campus_monitor"
    REDIS_URL: str = "redis://localhost:8880/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"
    API_KEY: str = "dev-api-key-change-in-production"

    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    ALERT_EMAIL_FROM: str = "campus-monitor@localhost"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
