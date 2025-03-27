import pytest
from templates.template_loader import TemplateLoader
from pathlib import Path


def test_template_loader_parses_fields(tmp_path):
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
    template_content = (
        "FIELD|Topic\n" "TEMPLATE|Description\n" "You selected: {{Topic}}"
    )
    tmpl_file = tmp_path / "task.tmpl"
    tmpl_file.write_text(template_content)

    loader = TemplateLoader(tmp_path, "task")
    output = loader.render_description({"Topic": "Automation"})

    assert "You selected: Automation" in output
