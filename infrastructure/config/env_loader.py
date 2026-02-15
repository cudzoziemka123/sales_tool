import os
from functools import lru_cache

from dotenv import find_dotenv, load_dotenv


class MissingEnvVarError(RuntimeError):
    """Raised when required environment variable is missing."""


@lru_cache(maxsize=1)
def ensure_env_loaded() -> None:
    """Load variables from `.env` once per process."""
    dotenv_path = find_dotenv(usecwd=True)
    load_dotenv(dotenv_path if dotenv_path else None, encoding="utf-8-sig")


def get_required_env(name: str) -> str:
    """Return required environment variable or raise explicit error."""
    ensure_env_loaded()
    value = os.getenv(name)
    if not value:
        raise MissingEnvVarError(f"Missing required environment variable: {name}")
    return value
