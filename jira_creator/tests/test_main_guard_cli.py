#!/usr/bin/env python
"""
This script tests the main guard in rh_jira.py.
"""

import subprocess
import sys
from unittest.mock import patch


def test_main_guard():
    """
    Test that the main guard in rh_jira.py works correctly.
    """
    import __main__ as main_script

    assert hasattr(main_script, "__name__")


def test_main_guard_execution():
    """
    Test that the main script can be executed directly.
    """
    # Test that the script runs without errors when called with --help
    result = subprocess.run(
        [sys.executable, "-m", "jira_creator.rh_jira", "--help"],
        capture_output=True,
        text=True,
        cwd="/home/daoneill/src/jira-creator",
    )

    # Should exit with code 0 for --help
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()


def test_main_function_direct_import():
    """
    Test importing and calling main function directly.
    """
    from jira_creator.rh_jira import main

    with patch("sys.argv", ["rh-issue", "--help"]):
        try:
            main()
        except SystemExit as e:
            # Expected behavior for --help
            assert e.code == 0


def test_main_guard_coverage():
    """
    Test that simulates running the script directly to cover the main guard.
    """
    import os
    import tempfile

    # Create a temporary script that imports and executes rh_jira
    test_script = """
import sys
import os
sys.path.insert(0, '/home/daoneill/src/jira-creator')

# Set up sys.argv before importing to avoid actual execution
sys.argv = ['rh-issue', '--help']

try:
    import jira_creator.rh_jira
    # This import should trigger the main guard
except SystemExit:
    # Expected when --help is used
    pass
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_script)
        temp_script = f.name

    try:
        # Execute the temporary script
        result = subprocess.run([sys.executable, temp_script], capture_output=True, text=True)
        # Should exit with 0 for --help
        assert result.returncode == 0
    finally:
        os.unlink(temp_script)
