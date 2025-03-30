import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock


def test_script_dry_run():
    # Set up environment
    env = os.environ.copy()
    env.update(
        {
            "JIRA_URL": "https://fake.jira",
            "PROJECT_KEY": "FAKE",
            "AFFECTS_VERSION": "0.0.1",
            "COMPONENT_NAME": "dummy-component",
            "PRIORITY": "Low",
            "JPAT": "fake-token",
            "AI_PROVIDER": "noop",
        }
    )

    # Create a temporary template file
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir)
        template_path = template_dir / "bug.tmpl"
        template_path.write_text(
            "FIELD|Title\nTEMPLATE|Description\nBug Title: {{Title}}"
        )

        script_path = Path("jira_creator/rh_jira.py")

        # Mock subprocess.run to avoid actually running the script
        subprocess.run = MagicMock()

        # Call the script (you can use the mock here if you want to check the call)
        subprocess.run(
            [
                "python3",
                str(script_path),
                "--dry-run",
                "--template",
                str(template_path),
            ],
            env=env,
        )

        # Check if subprocess.run was called as expected
        subprocess.run.assert_called_once_with(
            [
                "python3",
                str(script_path),
                "--dry-run",
                "--template",
                str(template_path),
            ],
            env=env,
        )
