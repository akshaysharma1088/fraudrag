"""Shared pytest configuration and fixtures."""
import os

# Set required env vars before any imports touch settings
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum-length-ok")
os.environ.setdefault("NEO4J_PASSWORD", "testpassword")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-placeholder-not-real")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://fraudrag:fraudrag@localhost:5432/fraudrag_test")
os.environ.setdefault("CHROMA_PERSIST_DIR", "/tmp/test-chroma")
os.environ.setdefault("BRONZE_RAW_PATH", "/tmp/test-bronze")
os.environ.setdefault("SILVER_NORMALIZED_PATH", "/tmp/test-silver")
os.environ.setdefault("GOLD_ANALYTICS_PATH", "/tmp/test-gold")
