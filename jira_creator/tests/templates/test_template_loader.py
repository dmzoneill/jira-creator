#!/usr/bin/env python
"""
This module contains unit tests for the `TemplateLoader` class, which is responsible for loading and processing
template files with specific fields and templates. The tests cover functionalities such as parsing fields,
rendering templates with provided data, handling missing template files, and returning joined strings from
template files. Each test function utilizes the `pytest` framework and operates within a temporary directory
to ensure isolation and cleanliness during testing.
"""

import pytest
from templates.template_loader import TemplateLoader


def test_template_loader_parses_fields(tmp_path):
    """
    Parses fields from a template file.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template file will be created.

    Side Effects:
    - Creates a template file with predefined fields in the specified temporary directory.
    """

    # Create a simple template file
    template_content = (
        "FIELD|Title\n"
        "FIELD|Body\n"
        "TEMPLATE|Description\n"
        "Title: {{Title}}\n"
        "Body: {{Body}}"
    )
    tmpl_file = tmp_path / "story.tmpl"
    tmpl_file.write_text(template_content)

    loader = TemplateLoader(tmp_path, "story")
    fields = loader.get_fields()

    assert fields == ["Title", "Body"]


def test_template_loader_renders_description(tmp_path):
    """
    Renders a template with a description field.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template file will be created.

    Side Effects:
    - Creates a template file in the specified temporary directory with predefined content.
    """

    template_content = (
        "FIELD|Topic\n" "TEMPLATE|Description\n" "You selected: {{Topic}}"
    )
    tmpl_file = tmp_path / "task.tmpl"
    tmpl_file.write_text(template_content)

    loader = TemplateLoader(tmp_path, "task")
    output = loader.render_description({"Topic": "Automation"})

    assert "You selected: Automation" in output


def test_template_loader_raises_file_not_found(tmp_path):
    """
    Load a test template from a temporary directory and raise a FileNotFoundError if the template file is not found.

    Arguments:
    - tmp_path (path): Path to a temporary directory where the template should be located.

    Exceptions:
    - FileNotFoundError: Raised if the template file is not found in the specified directory.
    """

    # Use a temporary directory with no templates inside
    fake_template_dir = tmp_path
    issue_type = "nonexistent"

    with pytest.raises(FileNotFoundError) as excinfo:
        TemplateLoader(fake_template_dir, issue_type)

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

    loader = TemplateLoader(template_dir=tmp_path, issue_type="sample")

    assert loader.template_lines == ["line1", "line2", "line3"]
    assert loader.get_template() == "line1\nline2\nline3"
