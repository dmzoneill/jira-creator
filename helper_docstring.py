#!/usr/bin/python
import argparse
import hashlib
import json
import os
import re
import time

import requests

system_prompt_general = f"""
You will be provided with a Python code.
Based on this, your task is to generate a Python docstring for it.
This is the docstring that goes at the top of the file.
The file may include multiple classes or other code.

Ensure the docstring follows Python's standard docstring conventions and provides
just enough detail to make the file understandable and usable without overwhelming the reader.

Please only return the docstring, enclosed in triple quotes, without any other explanation or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""

system_prompt_class = f"""
You will be provided with a Python class, including its code.
Based on this, your task is to generate a Python docstring for it.
Use the class signature and body to infer the purpose of the class,
the attributes it has, and any methods it includes.

Follow these guidelines to create the docstring:

1. Summary: Provide a concise summary of the class's purpose.
    Focus on what the class does and its main goal.
2. Attributes: List the attributes, their types, and a brief description
    of what each one represents.

Ensure the docstring follows Python's standard docstring conventions and provides
just enough detail to make the class understandable and usable without overwhelming the reader.

Please only return the docstring, enclosed in triple quotes, without any other explanation or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""

system_prompt_def = f"""
You will be provided with a Python function, including its code.
Based on this, your task is to generate a Python docstring for it.
Use the function signature and body to infer the purpose of the function,
the arguments it takes, the return value, and any exceptions it may raise.

Follow these guidelines to create the docstring:

1. Summary: Provide a concise summary of the function's purpose.
    Focus on what the function does and its main goal.
2. Arguments: List the parameters, their types, and a brief description
    of what each one represents.
3. Return: If the function has a return value, describe the return type
    and what it represents. If there's no return, OMIT THE SECTION.
4. Exceptions: If the function raises any exceptions, list them with descriptions.
    If no exceptions are raised, OMIT THE SECTION.
5. Side Effects (if applicable): If the function has side effects
    (e.g., modifies global state, interacts with external services), mention them.
    OMIT THE SECTION if it is not clear in the code.
6. Algorithm or Key Logic (optional): If the function is complex,
    provide a high-level outline of the logic or algorithm involved.
    OMIT THE SECTION if it is not clear in the code.

Ensure the docstring follows Python's standard docstring conventions and provides
just enough detail to make the function understandable and usable without overwhelming the reader.

Please only return the docstring, enclosed in triple quotes, without any other explanation or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""


class OpenAIProvider:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        if not self.api_key:
            raise EnvironmentError("AI_API_KEY not set in environment.")
        self.endpoint = "https://api.openai.com/v1/chat/completions"
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")

    def estimate_tokens(self, text: str) -> int:
        tokens = len(text) // 3  # Using the 3 bytes per token estimation
        return tokens

    def select_model(self, input):
        tokens = self.estimate_tokens(input)

        if tokens < 1000:  # For small files (under ~1000 tokens)
            model = "gpt-3.5-turbo"
        elif tokens < 10000:  # For medium files (under ~10000 tokens)
            model = "gpt-4o-mini"
        else:  # For large files (over ~10000 tokens)
            model = "gpt-4o"

        return model

    def improve_text(self, prompt: str, text: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body = {
            "model": self.select_model(text),
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.5,
        }

        response = requests.post(self.endpoint, json=body, headers=headers, timeout=300)
        if response.status_code == 200:
            res = response.json()["choices"][0]["message"]["content"].strip()
            return res

        raise Exception(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )


class Docstring:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lines = []
        self.ai = OpenAIProvider()
        self.line_index = 0
        self.cache_file = "docstring.cache"

        with open(self.file_path, "r") as file:
            self.lines = file.readlines()

        # Ensure cache file exists, create if necessary
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, "w") as cache:
                json.dump({}, cache)

        print(self.file_path)

    def _load_cache(self):
        with open(self.cache_file, "r") as cache:
            return json.load(cache)

    def _save_cache(self, cache):
        with open(self.cache_file, "w") as cache_file:
            json.dump(cache, cache_file, indent=4)

    def _generate_sha1(self, user_prompt):
        return hashlib.sha1(user_prompt.encode("utf-8")).hexdigest()

    def _get_current_timestamp(self):
        return int(time.time())

    def get_ai_docstring(self, sys_prompt, user_prompt):
        # Load the current cache
        cache = self._load_cache()

        sha1_hash = self._generate_sha1(user_prompt)

        # Check if file is in cache
        if self.file_path in cache:
            # Check if the user prompt's SHA1 is in the cache for this file
            for entry in cache[self.file_path]:
                if entry["sha1"] == sha1_hash:
                    # Update last_accessed timestamp
                    entry["last_accessed"] = self._get_current_timestamp()
                    # Save the updated cache
                    self._save_cache(cache)
                    # Return cached docstring if found
                    return entry["docstring"]

        # If no cache hit, call the AI and get the docstring
        res = self.ai.improve_text(sys_prompt, user_prompt)

        # Create a new cache entry with last_accessed timestamp
        new_entry = {
            "sha1": sha1_hash,
            "docstring": res,
            "last_accessed": self._get_current_timestamp(),
        }

        # Add new entry to the cache for the current file
        if self.file_path not in cache:
            cache[self.file_path] = []

        cache[self.file_path].append(new_entry)

        # Save the updated cache
        self._save_cache(cache)

        # Return the new docstring from AI
        return res

    def remove_old_entries(self, minutes):
        """Remove entries older than the specified number of minutes."""
        cache = self._load_cache()
        current_timestamp = self._get_current_timestamp()
        threshold_timestamp = current_timestamp - (minutes * 60)

        # Remove old entries for each file in the cache
        for file_path, entries in cache.items():
            cache[file_path] = [
                entry
                for entry in entries
                if "last_accessed" in entry
                and entry["last_accessed"] >= threshold_timestamp
            ]

        # Save the updated cache
        self._save_cache(cache)

    def wrap_text(self, text: str, max_length=120, indent=0):
        wrapped_lines = []
        lines = text.strip().splitlines()

        # Ensure indent is an integer
        try:
            indent = int(indent)
        except ValueError:
            indent = 0  # Default to 0 if it’s an invalid value

        spacer = ""
        if indent == 0:
            spacer = ""
        else:
            spacer = " " * (indent * 4)

        for line in lines:
            line = spacer + line.strip()
            while len(line) > max_length:
                # Find last space to split at
                split_at = line.rfind(" ", 0, max_length)
                if split_at == -1:
                    split_at = max_length  # no space found, split at max_length
                wrapped_lines.append(line[:split_at].rstrip())
                line = spacer + line[split_at:].strip()
            wrapped_lines.append(line)
        return wrapped_lines

    def count_and_divide_whitespace(self, line):
        leading_whitespace = len(line) - len(line.lstrip())
        if leading_whitespace == 0:
            return 0
        return leading_whitespace // 4

    def complete(self):
        # print("".join(self.lines))
        with open(self.file_path, "w") as file:
            file.write("".join(self.lines))

        self.remove_old_entries(1440 * 14)

    def generate_class_docstring(self):
        line = self.lines[self.line_index]
        class_definition = line
        print(class_definition.rstrip())
        prompt_class_code = [class_definition]

        if self.count_and_divide_whitespace(class_definition) > 0:
            self.line_index = self.line_index + 1
            return None

        t = self.line_index + 1
        # Collect all lines that belong to the class, including "pass" or single-line classes
        while (
            t < len(self.lines)
            and not self.lines[t].startswith("def")
            and not self.lines[t].startswith("class")
        ):
            prompt_class_code.append(self.lines[t].rstrip())
            t += 1

        class_docstring = self.get_ai_docstring(
            system_prompt_class, "\n".join(prompt_class_code)
        )
        class_docstring = self.wrap_text(class_docstring, max_length=120, indent=1)
        class_docstring[len(class_docstring) - 1] = (
            class_docstring[len(class_docstring) - 1] + "\n"
        )
        class_docstring = [line + "\n" for line in class_docstring]
        class_docstring[len(class_docstring) - 1] = (
            class_docstring[len(class_docstring) - 1].rstrip() + "\n"
        )

        # Check for existing docstring and replace it
        docstring_start_index = None
        docstring_end_index = None

        # Look for the class docstring (the second line should start with """ if it's there)
        if self.lines and self.lines[self.line_index + 1].strip().startswith('"""'):
            # Docstring exists, find the end of it
            docstring_start_index = (
                self.line_index + 1
            )  # The docstring starts from line after the class definition
            for i, line in enumerate(
                self.lines[self.line_index + 2 :], start=self.line_index + 2
            ):
                if line.strip().startswith('"""'):
                    docstring_end_index = i  # End of the docstring
                    break

        # If a docstring exists, replace it
        if docstring_start_index is not None and docstring_end_index is not None:
            self.lines = (
                self.lines[:docstring_start_index]
                + self.lines[docstring_end_index + 1 :]
            )

        # Insert the new docstring after the class definition
        self.lines = (
            self.lines[: self.line_index + 1]
            + class_docstring
            + self.lines[self.line_index + 1 :]
        )

        return True

    def generate_function_docstring(self):
        line = self.lines[self.line_index]
        def_definition = line
        print(def_definition.rstrip())
        prompt_def_code = [def_definition]

        indent_line = self.count_and_divide_whitespace(def_definition)
        spacer_line = "" if indent_line == 0 else " " * (indent_line * 4)
        spacer_line_minus = "" if indent_line < 2 else " " * ((indent_line - 1) * 4)
        spacer_line_plus = "" if indent_line == 0 else " " * ((indent_line + 1) * 4)

        t = self.line_index + 1
        # Collect all self.lines that belong to the function
        while t < len(self.lines):
            starts_with_def = self.lines[t].strip().startswith("def")

            # same indent
            if starts_with_def and self.lines[t].startswith(spacer_line):
                break

            # outside
            if starts_with_def and self.lines[t].startswith(spacer_line_minus):
                break

            # nested
            if starts_with_def and self.lines[t].startswith(spacer_line_plus):
                pass

            if self.lines[t].rstrip() != def_definition.strip():
                prompt_def_code.append(self.lines[t].rstrip())
            t += 1

        # Now that we have the full function signature, we generate the docstring
        indent = self.count_and_divide_whitespace(def_definition) + 1
        def_docstring = self.get_ai_docstring(
            system_prompt_def, "\n".join(prompt_def_code)
        )
        def_docstring = self.wrap_text(def_docstring, max_length=120, indent=indent)
        def_docstring[len(def_docstring) - 1] = (
            def_docstring[len(def_docstring) - 1] + "\n"
        )
        if def_definition.strip() == def_docstring[0].strip():
            def_docstring = def_docstring[1:]
        def_docstring = [line + "\n" for line in def_docstring]
        def_docstring[len(def_docstring) - 1] = (
            def_docstring[len(def_docstring) - 1].rstrip() + "\n"
        )

        # Handle one-liner docstring or multi-line docstring
        if self.line_index + 1 < len(self.lines):
            stripped_line = self.lines[self.line_index + 1].strip()
            if re.match(r'"""[\s\S]+?"""', stripped_line):
                # print(" -> Replacing one liner docstring")
                # This is a one-liner or multi-line docstring (we always replace with a multi-line docstring)
                self.lines = (
                    self.lines[: self.line_index + 1]
                    + def_docstring
                    + self.lines[self.line_index + 2 :]
                )
            else:
                # print(" -> Replacing multi-line docstring")
                # Replace the entire docstring if it's multi-line
                end_index = self.line_index + 2
                while end_index < len(self.lines) and not self.lines[
                    end_index
                ].strip().startswith('"""'):
                    end_index += 1

                if (
                    end_index < len(self.lines)
                    and self.lines[end_index].strip() == '"""'
                ):
                    # Found the end of the docstring, now replace the entire docstring block
                    self.lines = (
                        self.lines[: self.line_index + 1]
                        + def_docstring
                        + self.lines[end_index + 1 :]
                    )
        else:
            # If no docstring exists, simply insert the generated docstring
            self.lines = (
                self.lines[: self.line_index + 1]
                + def_docstring
                + self.lines[self.line_index + 1 :]
            )

        self.line_index = self.line_index + len(def_docstring)
        return True

    def should_add_file_docstring(self):
        # Split content into lines and remove empty lines
        lines = [line.strip() for line in self.lines if line.strip()]

        # Case 1: If the file is too short, skip file docstring
        if len(lines) <= 10:  # Assuming 10 lines or less is a short file
            # If there's only one function and it's self-explanatory, skip file-level docstring
            if lines.count("def") == 1 and "class" not in lines:
                return (
                    False  # No need for file-level docstring if the function is simple
                )

        # Case 2: If the file has a class and methods with docstrings, no need for a file docstring
        if "class" in lines:
            # Check if every function (i.e., starts with "def") is followed by a docstring (i.e., a triple quote on the next line)
            function_with_docstrings = True
            for i, line in enumerate(lines):
                if line.startswith("def"):  # If we find a function definition
                    # Check if the next non-empty line is a docstring
                    if i + 1 < len(lines) and not lines[i + 1].startswith('"""'):
                        function_with_docstrings = False
                        break
            if function_with_docstrings:
                return False  # Class and methods have docstrings, file docstring not necessary

        # Case 3: Otherwise, add file-level docstring if the file is sufficiently complex
        if len(lines) > 10 or "def" in lines:
            return (
                True  # File is sufficiently complex to warrant a file-level docstring
            )

        return False  # Default case: don't add file docstring if none of the above conditions apply

    def generate_file_docstring(self):
        # Check if we should add a file-level docstring
        # if not self.should_add_file_docstring():
        #     return 0  # Skip generating file-level docstring if not needed

        shebang = ""

        # Check if the first line starts with a shebang (e.g., #! anything)
        if self.lines and not self.lines[0].startswith("#!"):
            self.lines = ["#!/usr/bin/env python\n"] + self.lines
            shebang = "#!/usr/bin/env python\n"
        else:
            shebang = self.lines[0]

        # Check if there's already an existing file-level docstring or comment block
        # We assume the file-level docstring starts with triple quotes (""" or ''') and is at the top
        docstring_start_index = None
        docstring_end_index = None

        if self.lines and self.lines[1].strip().startswith('"""'):
            # If the second line starts with triple quotes, it may be a docstring
            docstring_start_index = 1  # The docstring starts from line 2
            for i, line in enumerate(self.lines[2:], start=2):
                if line.strip().startswith('"""'):
                    docstring_end_index = i  # End of the docstring
                    break

        # Generate new file-level docstring
        general_description = self.get_ai_docstring(
            system_prompt_general, "".join(self.lines)
        )
        general_description = self.wrap_text(
            general_description, max_length=120, indent=0
        )
        docstring = [line + "\n" for line in general_description]

        # If a docstring exists, replace it with the new one
        if docstring_start_index is not None and docstring_end_index is not None:
            self.lines = (
                self.lines[:docstring_start_index]
                + docstring
                + self.lines[docstring_end_index + 1 :]
            )
        else:
            # Insert the generated docstring directly after the shebang (no extra newline)
            self.lines = [shebang] + docstring + self.lines[1:]

        return len(docstring)

    def generate_docstrings(self):
        if len(self.lines) == 0:
            return

        self.line_index = self.generate_file_docstring()

        while self.line_index < len(self.lines):
            line = self.lines[self.line_index]

            # For classes, generate class docstring
            if line.strip().startswith("class "):
                if not self.generate_class_docstring():
                    continue  # Skip to the next line

            # For functions, generate function docstring
            elif line.strip().startswith("def "):
                if not self.generate_function_docstring():
                    continue  # Skip to the next line

            self.line_index = self.line_index + 1

        self.complete()


def process_file(file_path):
    """Process a single file by generating docstrings."""
    Docstring(file_path).generate_docstrings()


def process_directory(directory_path, recursive=False):
    """Process all Python files in the directory."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            # Only process Python files
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                process_file(file_path)

        # If not recursive, break after the first directory level
        if not recursive:
            break


def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Generate file-level docstrings for Python files."
    )
    parser.add_argument("path", help="Path to a Python file or directory.")
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively process all Python files in the directory.",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Check if the path is a file or directory
    if os.path.isfile(args.path):
        # If it's a file, process it directly
        process_file(args.path)
    elif os.path.isdir(args.path):
        # If it's a directory, process all Python files
        process_directory(args.path, recursive=args.recursive)
    else:
        print(f"Error: {args.path} is neither a valid file nor a directory.")


if __name__ == "__main__":
    main()
