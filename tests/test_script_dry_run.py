import os
import subprocess
from pathlib import Path
import tempfile


def test_script_dry_run(monkeypatch):
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

        script_path = Path("rh-jira.py")
        if not script_path.exists():
            return  # skip if script file not found

        result = subprocess.run(
            [
                "python",
                str(script_path),
                "create",
                "bug",
                "Example bug summary",
                "--dry-run",
            ],
            input="My test bug\n",
            capture_output=True,
            text=True,
            env={**env, "TEMPLATE_DIR": str(template_dir)},
        )

        assert result.returncode == 0
        assert "📦 DRY RUN ENABLED" in result.stdout
        assert "Bug Title: My test bug" in result.stdout
        assert '"summary": "Example bug summary"' in result.stdout
