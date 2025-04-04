import pytest
from templates.template_loader import TemplateLoader


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


def test_template_loader_raises_file_not_found(tmp_path):
    # Use a temporary directory with no templates inside
    fake_template_dir = tmp_path
    issue_type = "nonexistent"

    with pytest.raises(FileNotFoundError) as excinfo:
        TemplateLoader(fake_template_dir, issue_type)

    assert f"{issue_type}.tmpl" in str(excinfo.value)


def test_get_template_returns_joined_string(tmp_path):
    template_file = tmp_path / "sample.tmpl"
    template_content = "FIELD|description\nTEMPLATE|\nline1\nline2\nline3"
    template_file.write_text(template_content)

    loader = TemplateLoader(template_dir=tmp_path, issue_type="sample")

    assert loader.template_lines == ["line1", "line2", "line3"]
    assert loader.get_template() == "line1\nline2\nline3"
