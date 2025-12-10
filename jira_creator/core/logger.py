#!/usr/bin/env python
"""
Logging configuration for jira-creator.

This module provides centralized logging configuration with support for
different log levels and output formats.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from jira_creator.core.env_fetcher import EnvFetcher


class JiraLogger:
    """Centralized logger for jira-creator."""

    _instance: Optional[logging.Logger] = None
    _configured: bool = False

    @classmethod
    def get_logger(cls, name: str = "jira-creator") -> logging.Logger:
        """
        Get or create the configured logger instance.

        Arguments:
            name: Logger name (default: jira-creator)

        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._configured:
            cls._configure_logging()

        return logging.getLogger(name)

    @classmethod
    def _configure_logging(cls) -> None:
        """Configure the logging system based on environment variables."""
        if cls._configured:
            return

        # Get log level from environment (default: WARNING)
        log_level_str = EnvFetcher.get("JIRA_LOG_LEVEL", default="WARNING")
        log_level = getattr(logging, log_level_str.upper(), logging.WARNING)

        # Get log file path (optional)
        log_file = EnvFetcher.get("JIRA_LOG_FILE", default="")

        # Get log format preference
        log_format_type = EnvFetcher.get("JIRA_LOG_FORMAT", default="simple")

        # Define log formats
        formats = {
            "simple": "%(levelname)s: %(message)s",
            "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "debug": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        }

        log_format = formats.get(log_format_type, formats["simple"])

        # Create formatter
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

        # Get root logger
        root_logger = logging.getLogger("jira-creator")
        root_logger.setLevel(log_level)

        # Remove existing handlers
        root_logger.handlers.clear()

        # Add console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Add file handler if specified
        if log_file:
            try:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)

                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)

                root_logger.debug("Logging to file: %s", log_file)
            except (OSError, IOError) as e:
                root_logger.warning("Failed to create log file %s: %s", log_file, e)

        cls._configured = True
        root_logger.debug("Logging configured: level=%s, format=%s", log_level_str, log_format_type)

    @classmethod
    def reset(cls) -> None:
        """Reset logging configuration (primarily for testing)."""
        cls._configured = False
        logging.getLogger("jira-creator").handlers.clear()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Arguments:
        name: Optional logger name (defaults to jira-creator)

    Returns:
        logging.Logger: Configured logger instance
    """
    logger_name = f"jira-creator.{name}" if name else "jira-creator"
    return JiraLogger.get_logger(logger_name)
