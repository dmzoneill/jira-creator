#!/usr/bin/env python
"""
This module contains unit tests for the `EnvFetcher` class from the `core.env_fetcher` module.

The tests cover the following functionalities:
- Retrieving environment variables from the operating system.
- Accessing environment variables using the pytest context.
- Handling scenarios where requested environment variables are missing, ensuring that appropriate exceptions are raised.

Mock objects are utilized to simulate various environments, allowing for comprehensive testing without reliance on
actual environment variables. The tests validate the expected behavior of the `EnvFetcher` class's methods, including
the retrieval and fetching of environment variables.
"""

from unittest.mock import patch

import pytest

from jira_creator.core.env_fetcher import EnvFetcher
from jira_creator.exceptions.exceptions import MissingConfigVariable


def test_get_env_variable_from_os():
    """
    Retrieve an environment variable from the OS environment.

    Arguments:
    No arguments are passed explicitly, as the function internally fetches an environment variable named "JIRA_URL".

    Return:
    The function returns the value of the "JIRA_URL" environment variable, which is a string representing the URL
    "https://real-env.com".

    Side Effects:
    This function interacts with the OS environment variables to fetch the value of the specified variable.
    """

    with (
        patch.dict("os.environ", {"JIRA_URL": "https://real-env.com"}),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate non-pytest
        result = EnvFetcher.get("JIRA_URL")
        assert result == "https://real-env.com"


def test_get_env_variable_from_pytest_context():
    """
    Retrieve an environment variable using the pytest context.

    Arguments:
    No arguments.

    Return:
    No return value.

    Exceptions:
    No exceptions raised.
    """

    with patch.dict("sys.modules", {"pytest": True}):
        result = EnvFetcher.get("JIRA_PROJECT_KEY")
        assert result == "XYZ"


def test_get_env_variable_raises_if_missing():
    """
    This function tests the behavior of the 'get' method of the EnvFetcher class when a requested environment variable
    is missing. It simulates a real run environment with no environment variables set and asserts that the method
    raises a MissingConfigVariable exception when attempting to retrieve a missing variable.

    Arguments:
    No arguments.

    Exceptions:
    - MissingConfigVariable: Raised when the 'get' method of the EnvFetcher class is called with a missing variable.

    Side Effects:
    - Modifies the environment variables and sys.modules to simulate a scenario with no environment variables set.

    Return:
    No return value.
    """

    with (
        patch.dict("os.environ", {}, clear=True),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate real run, no env
        with pytest.raises(MissingConfigVariable) as exc_info:
            EnvFetcher.get("MISSING_VAR")

        assert "Missing required Jira environment variable" in str(exc_info.value)


def test_fetch_all_returns_expected_vars():
    """
    Fetches environment variables for the given keys and returns them as a dictionary.

    Arguments:
    - keys (list): A list of strings representing the keys of the environment variables to fetch.

    Return:
    - dict: A dictionary where keys are the input keys and values are the corresponding environment variable values.
    """

    with patch.dict("sys.modules", {"pytest": True}):
        result = EnvFetcher.fetch_all(["JIRA_PROJECT_KEY", "JIRA_COMPONENT_NAME"])
        assert result["JIRA_PROJECT_KEY"] == "XYZ"
        assert result["JIRA_COMPONENT_NAME"] == "backend"


def test_get_env_variable_with_default():
    """Test get method with default parameter."""
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate real run, no env
        result = EnvFetcher.get("MISSING_VAR", "default_value")
        assert result == "default_value"


def test_get_env_variable_template_dir_none():
    """Test get method for TEMPLATE_DIR when value is None."""
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate real run, no env
        result = EnvFetcher.get("TEMPLATE_DIR")
        # Should return the template default path
        assert "templates" in result


def test_get_env_variable_empty_with_default():
    """Test get method when value is empty string but default provided."""
    with (
        patch.dict("os.environ", {"TEST_VAR": ""}),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate real run
        result = EnvFetcher.get("TEST_VAR", "fallback_value")
        assert result == "fallback_value"
