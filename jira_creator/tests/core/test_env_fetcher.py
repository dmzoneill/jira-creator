from unittest.mock import patch

import pytest
from core.env_fetcher import EnvFetcher
from exceptions.exceptions import MissingConfigVariable


def test_get_env_variable_from_os():
    with (
        patch.dict("os.environ", {"JIRA_URL": "https://real-env.com"}),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate non-pytest
        result = EnvFetcher.get("JIRA_URL")
        assert result == "https://real-env.com"


def test_get_env_variable_from_pytest_context():
    with patch.dict("sys.modules", {"pytest": True}):
        result = EnvFetcher.get("PROJECT_KEY")
        assert result == "XYZ"


def test_get_env_variable_raises_if_missing():
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.dict("sys.modules", {}, clear=True),
    ):  # Simulate real run, no env
        with pytest.raises(MissingConfigVariable) as exc_info:
            EnvFetcher.get("MISSING_VAR")

        assert "Missing required Jira environment variable" in str(exc_info.value)


def test_fetch_all_returns_expected_vars():
    with patch.dict("sys.modules", {"pytest": True}):
        result = EnvFetcher.fetch_all(["PROJECT_KEY", "COMPONENT_NAME"])
        assert result["PROJECT_KEY"] == "XYZ"
        assert result["COMPONENT_NAME"] == "backend"
