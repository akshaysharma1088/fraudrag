"""Shared pytest configuration and fixtures."""
import pytest
import os

# Set required env vars before any imports
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum-length")
os.environ.setdefault("NEO4J_PASSWORD", "testpassword")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://fraudrag:fraudrag@localhost:5432/fraudrag_test")
