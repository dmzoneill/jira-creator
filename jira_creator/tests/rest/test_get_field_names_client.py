import json
import time
from unittest.mock import MagicMock, mock_open, patch


# Test for cache_fields when the file exists and is recent
def test_cache_fields_file_exists_and_recent(client):
    client.fields_cache_path = "/tmp/to/cache.json"

    # Mock os.path.exists and os.path.getmtime to simulate a recent file
    with (
        patch("os.path.exists", return_value=True),
        patch("os.path.getmtime", return_value=time.time()),
    ):
        with (
            patch(
                "builtins.open",
                mock_open(read_data=json.dumps([{"id": "1", "name": "Field 1"}])),
            ) as mocked_open,
            patch("os.makedirs") as _,
        ):
            fields = client.cache_fields()

            # Verify the returned fields
            assert fields == [{"id": "1", "name": "Field 1"}]
            # Ensure the file was opened for reading
            mocked_open.assert_called_once_with(client.fields_cache_path, "r")


# Test for cache_fields when the file does not exist or is old
def test_cache_fields_file_does_not_exist_or_old(client):
    client.fields_cache_path = "/tmp/to/cache.json"

    # Mock os.path.exists to return False (file doesn't exist)
    with patch("os.path.exists", return_value=False):
        # Mock _request to return a mock fields response
        with patch.object(
            client, "_request", return_value=[{"id": "1", "name": "Field 1"}]
        ):
            with (
                patch("os.makedirs"),
                patch("builtins.open", mock_open()) as mocked_file,
            ):
                fields = client.cache_fields()

                # Verify the fields are returned correctly from the _request mock
                assert fields == [{"id": "1", "name": "Field 1"}]
                # Ensure the cache directory was created
                # os.makedirs.assert_called_once_with(
                #    os.path.dirname(client.fields_cache_path), exist_ok=True
                # )
                # Ensure the file was opened for writing
                mocked_file.assert_called_once_with(client.fields_cache_path, "w")


# Test for get_field_name
def test_get_field_name(client):
    client.fields_cache_path = "/tmp/to/cache.json"

    # Mock cache_fields to return a mock fields list
    with patch.object(
        client, "cache_fields", return_value=[{"id": "1", "name": "Field 1"}]
    ):
        # Mocking requests.request to avoid triggering an actual API call
        with patch("requests.request") as mock_request:
            mock_request.return_value = MagicMock()  # Avoid API call
            field_name = client.get_field_name("1")

            # Verify the correct field name is returned
            assert field_name == "Field 1"

            # Test for a non-existing field ID
            field_name = client.get_field_name("nonexistent")
            assert field_name is None
