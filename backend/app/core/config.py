import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Xeno AI-Native Mini CRM"
    API_V1_STR: str = "/api/v1"
    

    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "xeno_crm")
    
    @property
    def DATABASE_URL(self) -> str:
        # Use Railway's injected DATABASE_URL if available
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            if env_url.startswith("postgres://"):
                env_url = env_url.replace("postgres://", "postgresql://", 1)
            return env_url

        user = self.POSTGRES_USER or "postgres"
        password = self.POSTGRES_PASSWORD or "postgres"
        host = self.POSTGRES_HOST or "localhost"
        port = self.POSTGRES_PORT or "5432"
        db = self.POSTGRES_DB or "xeno_crm"
        
        if not user.strip(): user = "postgres"
        if not password.strip(): password = "postgres"
        if not host.strip(): host = "localhost"
        if not port.strip(): port = "5432"
        if not db.strip(): db = "xeno_crm"
        
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        host = self.REDIS_HOST or "localhost"
        port = self.REDIS_PORT or "6379"
        if not host.strip(): host = "localhost"
        if not port.strip(): port = "6379"
        return f"redis://{host}:{port}/0"
        
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        host = self.REDIS_HOST or "localhost"
        port = self.REDIS_PORT or "6379"
        if not host.strip(): host = "localhost"
        if not port.strip(): port = "6379"
        return f"redis://{host}:{port}/0"


    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    class Config:
        case_sensitive = True

settings = Settings()
