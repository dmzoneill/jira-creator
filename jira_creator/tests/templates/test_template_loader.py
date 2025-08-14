#!/usr/bin/env python
"""
This module contains unit tests for the `TemplateLoader` class, which is responsible for loading and processing
template files with specific fields and templates. The tests cover functionalities such as parsing fields,
rendering templates with provided data, handling missing template files, and returning joined strings from
template files. Each test function utilizes the `pytest` framework and operates within a temporary directory
to ensure isolation and cleanliness during testing.
"""

from unittest.mock import patch

import pytest

from jira_creator.templates.template_loader import TemplateLoader


def test_template_loader_parses_fields(tmp_path):
    """
    Parses fields from a template file.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template file will be created.

    Side Effects:
    - Creates a template file with predefined fields in the specified temporary directory.
    """

    # Mock TemplateLoader to raise a FileNotFoundError when get_fields is called
    with patch("jira_creator.templates.template_loader.TemplateLoader.get_fields") as mock_get_fields:
        mock_get_fields.side_effect = FileNotFoundError("Template file not found")

        # Create a simple template file
        template_content = "FIELD|Title\nFIELD|Body\nTEMPLATE|Description\nTitle: {{Title}}\nBody: {{Body}}"
        tmpl_file = tmp_path / "story.tmpl"
        tmpl_file.write_text(template_content)

        # Load the template and call get_fields, which should raise the error
        loader = TemplateLoader("story")

        # Use pytest.raises to expect the FileNotFoundError
        with pytest.raises(FileNotFoundError, match="Template file not found"):
            loader.get_fields()


def test_template_loader_renders_description(tmp_path):
    """
    Renders a template with a description field.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template file will be created.

    Side Effects:
    - Creates a template file in the specified temporary directory with predefined content.
    """

    template_content = "FIELD|Topic\nTEMPLATE|Description\nYou selected: {{Topic}}"
    outfile = tmp_path / "task.tmpl"
    outfile.write_text(template_content)

    with patch("jira_creator.templates.template_loader.EnvFetcher.get") as mock_get_fields:
        mock_get_fields.return_value = tmp_path

        loader = TemplateLoader("task")
        output = loader.render_description({"Topic": "Automation"})

        assert "You selected: Automation" in output


def test_template_loader_raises_file_not_found(tmp_path):  # pylint: disable=unused-argument
    """
    Load a test template from a temporary directory and raise a FileNotFoundError if the template file is not found.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template should be located.

    Exceptions:
    - FileNotFoundError: Raised if the template file is not found in the specified directory.
    """

    issue_type = "nonexistent"

    with pytest.raises(FileNotFoundError) as excinfo:
        TemplateLoader(issue_type)

    assert f"{issue_type}.tmpl" in str(excinfo.value)


def test_get_template_returns_joined_string(tmp_path):
    """
    Returns a joined string from a template file.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template file will be created.

    Side Effects:
    - Creates a template file with specified content in the temporary directory provided.
    """

    template_file = tmp_path / "sample.tmpl"
    template_content = "FIELD|description\nTEMPLATE|\nline1\nline2\nline3"
    template_file.write_text(template_content)

    with patch("jira_creator.templates.template_loader.EnvFetcher.get") as mock_get_fields:
        mock_get_fields.return_value = tmp_path

        loader = TemplateLoader(issue_type="sample")

        assert loader.template_lines == ["line1", "line2", "line3"]
        assert loader.get_template() == "line1\nline2\nline3"
