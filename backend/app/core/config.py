from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "校园账号异常登录监测平台"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "mysql+pymysql://campus_user:campus123@localhost:3306/campus_monitor"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
