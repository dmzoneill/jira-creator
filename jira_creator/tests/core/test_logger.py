#!/usr/bin/env python
"""Tests for the logger module."""

import logging
from unittest.mock import patch

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.core.logger import JiraLogger, get_logger

# Add logging environment variables to EnvFetcher vars for testing
if not hasattr(EnvFetcher, "vars"):
    EnvFetcher.vars = {}

for var in ["JIRA_LOG_LEVEL", "JIRA_LOG_FILE", "JIRA_LOG_FORMAT"]:
    if var not in EnvFetcher.vars:
        EnvFetcher.vars[var] = ""


class TestJiraLogger:
    """Test cases for JiraLogger."""

    def setup_method(self):
        """Reset logger before each test."""
        JiraLogger.reset()

    def teardown_method(self):
        """Clean up after each test."""
        JiraLogger.reset()

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_default(self, mock_env):
        """Test getting logger with default settings."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "WARNING",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert logger is not None
        assert logger.name == "jira-creator"
        assert logger.level == logging.WARNING

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_debug_level(self, mock_env):
        """Test getting logger with DEBUG level."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "DEBUG",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert logger.level == logging.DEBUG

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_info_level(self, mock_env):
        """Test getting logger with INFO level."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert logger.level == logging.INFO

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_with_name(self, mock_env):
        """Test getting logger with custom name."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "WARNING",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger("custom")

        assert logger.name == "custom"

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_configure_logging_simple_format(self, mock_env):
        """Test logging configuration with simple format."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert len(logger.handlers) > 0
        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_configure_logging_detailed_format(self, mock_env):
        """Test logging configuration with detailed format."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "detailed",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert len(logger.handlers) > 0

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_configure_logging_debug_format(self, mock_env):
        """Test logging configuration with debug format."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "DEBUG",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "debug",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        assert logger.level == logging.DEBUG

    @patch("jira_creator.core.logger.EnvFetcher.get")
    @patch("builtins.open", create=True)
    @patch("pathlib.Path.mkdir")
    def test_configure_logging_with_file(self, mock_mkdir, mock_open_file, mock_env):
        """Test logging configuration with file output."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "/tmp/test.log",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = JiraLogger.get_logger()

        # Should have console handler + file handler
        assert len(logger.handlers) >= 1

    @patch("jira_creator.core.logger.EnvFetcher.get")
    @patch("builtins.open", side_effect=OSError("Permission denied"))
    def test_configure_logging_file_error(self, mock_open_file, mock_env):
        """Test logging configuration when file creation fails."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "/invalid/path/test.log",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        # Should not raise exception, just log warning
        logger = JiraLogger.get_logger()

        assert logger is not None
        # Should still have console handler
        assert len(logger.handlers) >= 1

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_singleton(self, mock_env):
        """Test that logger configuration is singleton."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        # Call get_logger multiple times to test singleton behavior
        JiraLogger.get_logger()
        JiraLogger.get_logger()

        # Should be configured only once
        assert JiraLogger._configured is True

    def test_reset(self):
        """Test resetting logger configuration."""
        with patch("jira_creator.core.logger.EnvFetcher.get", return_value=""):
            JiraLogger.get_logger()
            assert JiraLogger._configured is True

            JiraLogger.reset()
            assert JiraLogger._configured is False

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_function(self, mock_env):
        """Test the get_logger convenience function."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = get_logger()

        assert logger.name == "jira-creator"

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_get_logger_function_with_name(self, mock_env):
        """Test get_logger function with custom name."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = get_logger("plugin")

        assert logger.name == "jira-creator.plugin"

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_logger_actual_logging(self, mock_env, caplog):
        """Test that logger actually logs messages."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "DEBUG",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        logger = get_logger()

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text

    @patch("jira_creator.core.logger.EnvFetcher.get")
    def test_configure_logging_already_configured(self, mock_env):
        """Test that _configure_logging returns early if already configured."""
        mock_env.side_effect = lambda key, default="": {
            "JIRA_LOG_LEVEL": "INFO",
            "JIRA_LOG_FILE": "",
            "JIRA_LOG_FORMAT": "simple",
        }.get(key, default)

        # First call - should configure
        JiraLogger.get_logger()
        assert JiraLogger._configured is True

        # Second call - should return early on line 43
        JiraLogger._configure_logging()

        # Still configured
        assert JiraLogger._configured is True
