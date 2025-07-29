"""
Test Flask configuration best practices implementation
"""
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask

from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, generate_secret_key, get_config_class


class TestConfiguration(unittest.TestCase):
    """Test configuration classes and patterns"""

    def setUp(self):
        """Set up test fixtures"""
        # Store original environment
        self.original_env = dict(os.environ)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_config_class_selection(self):
        """Test that the correct config class is selected based on environment"""
        # Clear pytest detection for this test
        original_argv = sys.argv.copy()

        try:
            # Test development
            os.environ["FLASK_ENV"] = "development"
            # Temporarily modify sys.argv to avoid pytest detection
            sys.argv = ["python", "test_script.py"]
            from importlib import reload

            import config

            reload(config)
            self.assertEqual(config.get_config_class(), config.DevelopmentConfig)

            # Test production (default)
            os.environ["FLASK_ENV"] = "production"
            reload(config)
            self.assertEqual(config.get_config_class(), config.ProductionConfig)

            # Test testing
            os.environ["FLASK_ENV"] = "testing"
            reload(config)
            self.assertEqual(config.get_config_class(), config.TestingConfig)

            # Test unknown environment defaults to production
            os.environ["FLASK_ENV"] = "unknown"
            reload(config)
            self.assertEqual(config.get_config_class(), config.ProductionConfig)
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_flask_prefixed_env_vars(self):
        """Test that Flask prefixed environment variables are loaded"""
        app = Flask(__name__)

        # Set Flask-prefixed environment variables
        os.environ["FLASK_MAX_MESSAGE_LENGTH"] = "5000"
        os.environ["FLASK_CLAUDE_MODEL"] = "claude-3-opus-20240229"
        os.environ["FLASK_SECRET_KEY"] = "test-secret-key-123"

        # Initialize configuration
        config_class = DevelopmentConfig
        config_class.init_app(app)

        # Check that Flask prefixed vars are loaded
        self.assertEqual(app.config["MAX_MESSAGE_LENGTH"], "5000")
        self.assertEqual(app.config["CLAUDE_MODEL"], "claude-3-opus-20240229")
        self.assertEqual(app.config["SECRET_KEY"], "test-secret-key-123")

    def test_development_config_validation(self):
        """Test development configuration validation"""
        # Create a new app for each test
        app = Flask(__name__, instance_relative_config=True)

        # Clear any existing config
        app.config.clear()

        # Valid development config
        os.environ["FLASK_SECRET_KEY"] = "dev-key-long-enough-12345678"
        os.environ["FLASK_MAX_MESSAGE_LENGTH"] = "1000"

        # Should not raise an exception
        try:
            DevelopmentConfig.init_app(app)
        except Exception as e:
            self.fail(f"DevelopmentConfig.init_app() raised {type(e)} unexpectedly: {e}")

        # Create a fresh app for invalid config test
        app2 = Flask(__name__, instance_relative_config=True)
        app2.config.clear()

        # Invalid numeric value should raise error
        os.environ["FLASK_MAX_MESSAGE_LENGTH"] = "invalid"
        with self.assertRaises(ValueError):
            DevelopmentConfig.init_app(app2)

    def test_production_config_validation(self):
        """Test production configuration validation (strict)"""
        # Missing SECRET_KEY should fail
        app = Flask(__name__, instance_relative_config=True)
        app.config.clear()

        # Clear SECRET_KEY from environment
        for key in ["FLASK_SECRET_KEY", "SECRET_KEY"]:
            if key in os.environ:
                del os.environ[key]

        with self.assertRaises(ValueError) as context:
            ProductionConfig.init_app(app)
        self.assertIn("SECRET_KEY is required", str(context.exception))

        # Test insecure SECRET_KEY
        app2 = Flask(__name__, instance_relative_config=True)
        app2.config.clear()
        os.environ["FLASK_SECRET_KEY"] = "dev-secret-key-not-for-production"

        with self.assertRaises(ValueError) as context:
            ProductionConfig.init_app(app2)
        self.assertIn("cannot use default development values", str(context.exception))

        # Test short SECRET_KEY
        app3 = Flask(__name__, instance_relative_config=True)
        app3.config.clear()
        os.environ["FLASK_SECRET_KEY"] = "short"

        with self.assertRaises(ValueError) as context:
            ProductionConfig.init_app(app3)
        self.assertIn("must be at least 32 characters", str(context.exception))

    def test_testing_config(self):
        """Test testing configuration"""
        app = Flask(__name__)

        # Testing config should be lenient
        TestingConfig.init_app(app)

        self.assertTrue(app.config["TESTING"])
        self.assertEqual(app.config["SECRET_KEY"], "test-secret-key")
        self.assertEqual(app.config["MAX_MESSAGE_LENGTH"], 1000)

    def test_generate_secret_key(self):
        """Test secret key generation"""
        key = generate_secret_key()

        # Should be a string
        self.assertIsInstance(key, str)

        # Should be 64 characters (32 bytes in hex)
        self.assertEqual(len(key), 64)

        # Should be different each time
        key2 = generate_secret_key()
        self.assertNotEqual(key, key2)

        # Should be valid hex
        int(key, 16)  # Should not raise ValueError

    def test_config_inheritance(self):
        """Test that configuration classes properly inherit from base Config"""
        app = Flask(__name__)

        # Test that all config classes have required attributes
        for config_class in [Config, DevelopmentConfig, ProductionConfig, TestingConfig]:
            # Should have init_app method
            self.assertTrue(hasattr(config_class, "init_app"))
            self.assertTrue(callable(config_class.init_app))

            # Should have validate_config method
            self.assertTrue(hasattr(config_class, "validate_config"))
            self.assertTrue(callable(config_class.validate_config))

    def test_backward_compatibility(self):
        """Test that legacy environment variables still work"""
        app = Flask(__name__)

        # Set legacy environment variables
        os.environ["SECRET_KEY"] = "legacy-secret-key-12345678901234567890"
        os.environ["MAX_MESSAGE_LENGTH"] = "8000"
        os.environ["CLAUDE_MODEL"] = "claude-3-haiku-20240307"

        # Initialize with development config
        DevelopmentConfig.init_app(app)

        # Legacy variables should still work if FLASK_ versions aren't set
        # Note: FLASK_ prefixed vars take precedence if set
        self.assertIn("SECRET_KEY", app.config)


if __name__ == "__main__":
    unittest.main()
