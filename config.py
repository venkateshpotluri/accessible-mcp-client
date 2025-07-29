"""
Configuration management for the Accessible MCP Client.

This module implements Flask's recommended configuration patterns using
configuration classes and environment variable loading best practices.
"""
import os
import secrets
from typing import Optional


class Config:
    """Base configuration class with common settings."""

    # Flask core settings
    SECRET_KEY: Optional[str] = None

    # Application settings
    MAX_MESSAGE_LENGTH: int = 10000
    MAX_SESSION_TITLE_LENGTH: int = 200

    # Claude AI settings
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4000

    # MCP settings
    MCP_TIMEOUT: int = 30
    MAX_SERVERS: int = 10

    # Anthropic API
    ANTHROPIC_API_KEY: Optional[str] = None

    # Server settings
    PORT: int = 5000

    @classmethod
    def init_app(cls, app) -> None:
        """Initialize configuration for the Flask app."""
        # Load from this config class first (provides defaults)
        app.config.from_object(cls)

        # Load environment variables with FLASK_ prefix (overrides defaults)
        app.config.from_prefixed_env()

        # Validate required configuration
        cls.validate_config(app)

    @staticmethod
    def validate_config(app) -> None:
        """Validate that required configuration values are present."""
        errors = []

        # Check SECRET_KEY
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key:
            errors.append("SECRET_KEY is required but not set")
        elif secret_key == "your-secret-key-change-in-production":
            if not app.config.get("TESTING") and os.getenv("FLASK_ENV") != "development":
                errors.append(
                    "SECRET_KEY is still set to the default insecure value. "
                    'Generate a secure key using: python -c "import secrets; print(secrets.token_hex(32))"'
                )

        # Validate numeric settings
        try:
            max_msg_len = int(app.config.get("MAX_MESSAGE_LENGTH", 10000))
            if max_msg_len <= 0:
                errors.append("MAX_MESSAGE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            errors.append("MAX_MESSAGE_LENGTH must be a valid integer")

        try:
            max_title_len = int(app.config.get("MAX_SESSION_TITLE_LENGTH", 200))
            if max_title_len <= 0:
                errors.append("MAX_SESSION_TITLE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            errors.append("MAX_SESSION_TITLE_LENGTH must be a valid integer")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)


class DevelopmentConfig(Config):
    """Development configuration."""

    # Use insecure default only in development
    SECRET_KEY = "dev-secret-key-not-for-production"

    @staticmethod
    def validate_config(app) -> None:
        """Development-specific validation (more lenient)."""
        # Only validate that values are reasonable, not security
        try:
            max_msg_len = int(app.config.get("MAX_MESSAGE_LENGTH", 10000))
            if max_msg_len <= 0:
                raise ValueError("MAX_MESSAGE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("MAX_MESSAGE_LENGTH must be a valid integer")

        try:
            max_title_len = int(app.config.get("MAX_SESSION_TITLE_LENGTH", 200))
            if max_title_len <= 0:
                raise ValueError("MAX_SESSION_TITLE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("MAX_SESSION_TITLE_LENGTH must be a valid integer")


class ProductionConfig(Config):
    """Production configuration with enhanced security."""

    @staticmethod
    def validate_config(app) -> None:
        """Production-specific validation (strict)."""
        errors = []

        # Strict SECRET_KEY validation
        secret_key = app.config.get("SECRET_KEY")
        if not secret_key:
            errors.append("SECRET_KEY is required in production")
        elif len(secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters long in production")
        elif secret_key in ["dev-secret-key-not-for-production", "your-secret-key-change-in-production"]:
            errors.append("SECRET_KEY cannot use default development values in production")

        # Validate numeric settings (same as base class)
        try:
            max_msg_len = int(app.config.get("MAX_MESSAGE_LENGTH", 10000))
            if max_msg_len <= 0:
                errors.append("MAX_MESSAGE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            errors.append("MAX_MESSAGE_LENGTH must be a valid integer")

        try:
            max_title_len = int(app.config.get("MAX_SESSION_TITLE_LENGTH", 200))
            if max_title_len <= 0:
                errors.append("MAX_SESSION_TITLE_LENGTH must be a positive integer")
        except (ValueError, TypeError):
            errors.append("MAX_SESSION_TITLE_LENGTH must be a valid integer")

        if errors:
            error_msg = "Production configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            raise ValueError(error_msg)


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SECRET_KEY = "test-secret-key"

    # Smaller limits for testing
    MAX_MESSAGE_LENGTH = 1000
    MAX_SESSION_TITLE_LENGTH = 50

    @staticmethod
    def validate_config(app) -> None:
        """Testing-specific validation (minimal)."""
        # In testing, we're less strict about configuration
        pass


def get_config_class():
    """Get the appropriate configuration class based on environment."""
    env = os.getenv("FLASK_ENV", "").lower()

    # Special handling for pytest runs - only if no explicit FLASK_ENV is set
    import sys

    if ("pytest" in sys.modules or "pytest" in " ".join(sys.argv)) and not env:
        return TestingConfig

    if env == "development":
        return DevelopmentConfig
    elif env == "testing":
        return TestingConfig
    else:
        # Default to production for safety
        return ProductionConfig


def generate_secret_key() -> str:
    """Generate a secure random secret key."""
    return secrets.token_hex(32)
