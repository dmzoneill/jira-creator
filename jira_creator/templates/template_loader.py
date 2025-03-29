from pathlib import Path
from typing import List


class TemplateLoader:
    def __init__(self, template_dir: Path, issue_type: str):
        self.template_path = template_dir / f"{issue_type}.tmpl"
        if not self.template_path.exists():
            err = f"Template file not found: {self.template_path}"
            raise FileNotFoundError(err)
        self.fields: List[str] = []
        self.template_lines: List[str] = []
        self._load_template()

    def _load_template(self):
        in_template = False
        with open(self.template_path, "r") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("FIELD|"):
                    self.fields.append(line.split("|", 1)[1])
                elif line.startswith("TEMPLATE|"):
                    in_template = True
                elif in_template:
                    self.template_lines.append(line)

    def get_fields(self):
        return self.fields

    def get_template(self):
        return "\n".join(self.template_lines)

    def render_description(self, values: dict):
        description = ""
        for line in self.template_lines:
            while "{{" in line and "}}" in line:
                start = line.find("{{") + 2
                end = line.find("}}")
                placeholder = line[start:end]
                value = values.get(placeholder, "")
                line = line.replace(f"{{{{{placeholder}}}}}", value)
            description += line + "\n"
        return description
