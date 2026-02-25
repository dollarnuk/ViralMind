from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "ViralMind"
    API_V1_STR: str = "/api/v1"
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    DOWNLOAD_DIR: str = "downloads"
    OUTPUT_DIR: str = "output"
    FILE_RETENTION_HOURS: int = 24
    
    # Ensure directories exist
    @property
    def ensure_dirs(self):
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
settings.ensure_dirs
