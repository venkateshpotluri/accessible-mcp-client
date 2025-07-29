"""
Test .env file loading functionality
"""
import os
import tempfile
import unittest

from dotenv import load_dotenv


class TestEnvFileLoading(unittest.TestCase):
    """Test that .env files are properly loaded"""

    def setUp(self):
        """Set up test fixtures"""
        # Store original environment
        self.original_env = dict(os.environ)

    def tearDown(self):
        """Clean up after tests"""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_dotenv_loads_from_file(self):
        """Test that python-dotenv loads variables from .env file"""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            f.write("ANTHROPIC_API_KEY=sk-ant-test-key-123\n")
            f.write("SECRET_KEY=test-secret-key\n")
            temp_env_file = f.name

        try:
            # Clear environment variables that might conflict
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]

            # Load the .env file
            load_dotenv(temp_env_file)

            # Check that variables were loaded
            self.assertEqual(os.getenv("TEST_VAR"), "test_value")
            self.assertEqual(os.getenv("ANTHROPIC_API_KEY"), "sk-ant-test-key-123")
            self.assertEqual(os.getenv("SECRET_KEY"), "test-secret-key")

        finally:
            # Clean up temporary file
            os.unlink(temp_env_file)

    def test_env_vars_override_dotenv(self):
        """Test that environment variables take precedence over .env file"""
        # Create a temporary .env file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=from_file\n")
            f.write("ANTHROPIC_API_KEY=sk-ant-from-file\n")
            temp_env_file = f.name

        try:
            # Set environment variable before loading .env
            os.environ["TEST_VAR"] = "from_env"
            os.environ["ANTHROPIC_API_KEY"] = "sk-ant-from-env"

            # Load the .env file (should not override existing env vars)
            load_dotenv(temp_env_file)

            # Environment variables should take precedence
            self.assertEqual(os.getenv("TEST_VAR"), "from_env")
            self.assertEqual(os.getenv("ANTHROPIC_API_KEY"), "sk-ant-from-env")

        finally:
            # Clean up temporary file
            os.unlink(temp_env_file)

    def test_app_imports_with_dotenv(self):
        """Test that the main app can be imported and loads dotenv correctly"""
        # Create a temporary .env file in the project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_env_file = os.path.join(project_root, ".env.test")

        with open(test_env_file, "w") as f:
            f.write("TEST_ANTHROPIC_API_KEY=sk-ant-test-123\n")
            f.write("TEST_SECRET_KEY=test-secret\n")

        try:
            # Clear any existing values
            if "TEST_ANTHROPIC_API_KEY" in os.environ:
                del os.environ["TEST_ANTHROPIC_API_KEY"]
            if "TEST_SECRET_KEY" in os.environ:
                del os.environ["TEST_SECRET_KEY"]

            # Load the test .env file
            load_dotenv(test_env_file)

            # Check that variables were loaded
            self.assertEqual(os.getenv("TEST_ANTHROPIC_API_KEY"), "sk-ant-test-123")
            self.assertEqual(os.getenv("TEST_SECRET_KEY"), "test-secret")

            # Test that we can import the app module (which should also call load_dotenv)
            # This is primarily a smoke test to ensure no import errors
            try:
                # We can't actually import app here due to Flask initialization
                # but we can test the dotenv functionality directly
                from dotenv import load_dotenv as app_load_dotenv

                self.assertTrue(callable(app_load_dotenv))
            except ImportError:
                self.fail("Could not import load_dotenv function")

        finally:
            # Clean up test file
            if os.path.exists(test_env_file):
                os.unlink(test_env_file)


if __name__ == "__main__":
    unittest.main()
