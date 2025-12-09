from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Schwab Options Tracker"
    API_V1_STR: str = "/api"
    
    # Security
    SECRET_KEY: str = "CHANGE_ME"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 8 days
    
    # Database
    SQLITE_DB_PATH: str = "/data/schwab_tracker.db"
    
    # Schwab API
    SCHWAB_APP_KEY: str = ""
    SCHWAB_APP_SECRET: str = ""
    REDIRECT_URI: str = "https://127.0.0.1:8000/api/auth/callback" # Example
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
