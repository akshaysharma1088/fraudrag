"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # App
    APP_NAME: str = "FraudRAG"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Database (PostgreSQL – metadata & audit)
    DATABASE_URL: str = Field(default="postgresql+asyncpg://fraudrag:fraudrag@localhost:5432/fraudrag")

    # Neo4j Knowledge Graph
    NEO4J_URI: str = Field(default="bolt://localhost:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="fraudrag123")
    NEO4J_DATABASE: str = Field(default="neo4j")

    # Redis (caching & session)
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # AWS
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_BRONZE: str = "fraudrag-bronze"
    S3_BUCKET_SILVER: str = "fraudrag-silver"
    S3_BUCKET_GOLD: str = "fraudrag-gold"

    # LLM
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"  # "openai" | "anthropic"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4096
    EMBEDDING_MODEL: str = "text-embedding-3-large"

    # Vector Store
    CHROMA_PERSIST_DIR: str = "./data/chroma"
    CHROMA_COLLECTION: str = "statement_embeddings"

    # Fraud Detection Thresholds
    FRAUD_SCORE_HIGH_RISK: float = 0.75
    FRAUD_SCORE_MEDIUM_RISK: float = 0.45
    FRAUD_SCORE_LOW_RISK: float = 0.20

    # OCR
    TESSERACT_CMD: Optional[str] = None
    OCR_LANGUAGE: str = "eng"

    # Security
    SECRET_KEY: str = Field(default="change-me-in-production-32-chars-min")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # Medallion Pipeline
    BRONZE_RAW_PATH: str = "./data/bronze"
    SILVER_NORMALIZED_PATH: str = "./data/silver"
    GOLD_ANALYTICS_PATH: str = "./data/gold"
    SPARK_MASTER: str = "local[*]"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
