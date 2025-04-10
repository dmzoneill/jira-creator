from commands.cli_validate_issue import (  # isort: skip # pylint: disable=E0611
    load_and_cache_issue,
    load_cache,
    save_cache,
)  # isort: skip


def test_mock_load_cache(mock_load_cache):
    result = load_cache()
    assert isinstance(result, dict)


def test_mock_save_cache(mock_save_cache):
    save_cache({"AAP-test_mock_save_cache": {"summary_hash": "data"}})
    # mock_save_cache.assert_called_once()


def test_mock_load_and_cache_issue(mock_load_and_cache_issue):
    result, _ = load_and_cache_issue("AAP-test_mock_save_cache")
    assert result == {"AAP-test_mock_save_cache": {"summary_hash": "data"}}
