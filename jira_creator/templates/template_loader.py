#!/usr/bin/env python
"""
This module provides the TemplateLoader class for loading and rendering templates used in generating issue descriptions.

The TemplateLoader class allows for the initialization with a specific template directory and issue type, and includes
methods to:
- Load a template file and extract field names and content.
- Retrieve the list of fields defined in the template.
- Get the complete template content as a string.
- Render a description by replacing placeholders in the template with values from a provided dictionary.

Usage of this module is intended for applications that require dynamic generation of text based on templates, such as
issue tracking systems or reporting tools.
"""

from pathlib import Path
from typing import Dict, List


class TemplateLoader:
    """
    Class for loading and processing template files for generating issue descriptions.

    Attributes:
    - template_path (Path): The path to the template file for the specified issue type.
    - fields (List[str]): A list of field names extracted from the template file.
    - template_lines (List[str]): A list of lines comprising the template content.

    Methods:
    - __init__(template_dir: Path, issue_type: str): Initializes the TemplateLoader by loading the template file.
    - _load_template(): Private method to read and parse the template file, extracting fields and template content.
    - get_fields(): Returns the list of field names extracted from the template.
    - get_template(): Returns the template content as a single string.
    - render_description(values: Dict[str, str]) -> str: Processes the template content by replacing placeholders with
    provided values and returns the rendered description.
    """

    def __init__(self, template_dir: Path, issue_type: str) -> None:
        """
        Initialize a new instance of the class with the provided template directory and issue type.

        Arguments:
        - template_dir (Path): The directory where the template files are stored.
        - issue_type (str): The type of the issue for which the template is being loaded.

        Exceptions:
        - FileNotFoundError: Raised if the template file corresponding to the provided issue type is not found in the
        template directory.

        Side Effects:
        - Initializes instance variables 'template_path', 'fields', and 'template_lines'.
        - Calls the '_load_template' method to load the template file content.
        """

        self.template_path: Path = template_dir / f"{issue_type}.tmpl"
        if not self.template_path.exists():
            err = f"Template file not found: {self.template_path}"
            raise FileNotFoundError(err)
        self.fields: List[str] = []
        self.template_lines: List[str] = []
        self._load_template()

    def _load_template(self) -> None:
        """
        Load a template from a file specified by 'template_path' and extract fields and template lines.

        Arguments:
        - self: The object instance.

        Side Effects:
        - Modifies the 'fields' list attribute by appending extracted field names.
        - Modifies the 'template_lines' list attribute by appending lines of the template.
        """

        in_template: bool = False
        with open(self.template_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("FIELD|"):
                    self.fields.append(line.split("|", 1)[1])
                elif line.startswith("TEMPLATE|"):
                    in_template = True
                elif in_template:
                    self.template_lines.append(line)

    def get_fields(self) -> List[str]:
        """
        Retrieve and return the fields stored in the object.

        Arguments:
        - self: The object instance.

        Return:
        - List[str]: The fields stored in the object.
        """

        return self.fields

    def get_template(self) -> str:
        """
        Return the template content as a single string by joining the lines.

        Arguments:
        - self: The object instance.

        Return:
        - str: A single string representing the template content.
        """

        return "\n".join(self.template_lines)

    def render_description(self, values: Dict[str, str]) -> str:
        """
        Render the description using a template and provided values.

        Arguments:
        - self: the object instance
        - values (Dict[str, str]): A dictionary containing placeholder-value pairs to substitute in the template.

        Return:
        - str: The rendered description after replacing all placeholders with corresponding values.
        """

        description: str = ""
        for line in self.template_lines:
            while "{{" in line and "}}" in line:
                start: int = line.find("{{") + 2
                end: int = line.find("}}")
                placeholder: str = line[start:end]
                value: str = values.get(placeholder, "")
                line = line.replace(f"{{{{{placeholder}}}}}", value)
            description += line + "\n"
        return description
