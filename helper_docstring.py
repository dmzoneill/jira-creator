#!/usr/bin/python
import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time

import requests

system_prompt_general = """
You will be provided with a Python code.
Based on this, your task is to generate a Python docstring for it.
This is the docstring that goes at the top of the file.
The file may include multiple classes or other code.

Ensure the docstring follows Python's standard docstring conventions and provides
just enough detail to make the file understandable and usable without overwhelming the reader.

Please only return the docstring, enclosed in triple quotes, without any other explanation
or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""

system_prompt_class = """
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

Please only return the docstring, enclosed in triple quotes, without any other
explanation or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""

system_prompt_def = """
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

Please only return the docstring, enclosed in triple quotes, without any other
explanation or additional text. The format should be:

\"\"\"
<docstring content here>
\"\"\"

Make sure to follow the format precisely and provide only the docstring content.
"""


class OpenAICost:
    # Static member to track the total cost
    cost = 0
    costs = []  # A list to store the individual request costs

    @staticmethod
    def send_cost(tokens, model):
        # The cost calculation can vary based on the model and tokens
        model_costs = {
            "gpt-3.5-turbo": 0.002,  # Example cost per 1k tokens
            "gpt-4o-mini": 0.003,  # Example cost per 1k tokens
            "gpt-4o": 0.005,  # Example cost per 1k tokens
        }

        cost_per_token = model_costs.get(model, 0)
        cost = (tokens / 1000) * cost_per_token  # Cost is proportional to tokens

        OpenAICost.cost += cost
        OpenAICost.costs.append(cost)

    @staticmethod
    def print_cost_metrics():
        print(f"\nTotal Cost: ${OpenAICost.cost:.4f}")
        if OpenAICost.costs:
            print(
                f"    Average Cost per Request: ${statistics.mean(OpenAICost.costs):.4f}"
            )
            print(f"    Max Cost for a Request: ${max(OpenAICost.costs):.4f}")
            print(f"    Min Cost for a Request: ${min(OpenAICost.costs):.4f}")
            if len(OpenAICost.costs) > 1:
                print(
                    f"    Standard Deviation of Cost: ${statistics.stdev(OpenAICost.costs):.4f}"
                )
        else:
            print("    No costs recorded.")


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

        OpenAICost.send_cost(tokens, model)

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
            result = res
            # Count the occurrences of '"""'
            occurrences = result.count('"""')
            occurrences_backtick = result.count("```")

            # Check if there are more than two occurrences
            if occurrences > 2:
                # Find the positions of the first and second occurrences
                first_pos = result.find('"""')
                second_pos = result.find('"""', first_pos + 1)

                # Get everything from the first '"""' to the second '"""', inclusive
                result = result[first_pos : second_pos + 3]  # Include the second '"""'

            if occurrences_backtick > 2:
                # Find the positions of the first and second occurrences
                first_pos = result.find("```")
                second_pos = result.find("```", first_pos + 1)

                # Get everything from the first '"""' to the second '"""', inclusive
                result = result[first_pos : second_pos + 3]  # Include the second '"""'

            return result
        raise Exception(
            f"OpenAI API call failed: {response.status_code} - {response.text}"
        )


class Docstring:
    def __init__(self, file_path, debug=False, exit=False):
        self.file_path = file_path
        self.lines = []
        self.ai = OpenAIProvider()
        self.line_index = 0
        self.multiline_index = 0
        self.cache_file = "docstring.cache"
        self.debug = debug
        self.exit = exit

        with open(self.file_path, "r") as file:
            self.lines = file.readlines()

        # Ensure cache file exists, create if necessary
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, "w") as cache:
                json.dump({}, cache)

        self._load_cache()

        print(" -> " + self.file_path)

    def print_debug(self, title, out):
        if not self.debug:
            return

        print("=====================================================")
        print("=====================================================")
        print(" > > " + title)
        print("=====================================================")
        out = "".join(out) if isinstance(out, list) else out
        print(out)
        print("=====================================================")
        print("=====================================================")

    def _load_cache(self):
        with open(self.cache_file, "r") as cache:
            self.cache = json.load(cache)

    def _save_cache(self):
        with open(self.cache_file, "w") as cache_file:
            json.dump(self.cache, cache_file, indent=4)

    def _generate_sha1(self, user_prompt):
        return hashlib.sha1(user_prompt.encode("utf-8")).hexdigest()

    def _get_current_timestamp(self):
        return int(time.time())

    def get_ai_docstring(self, sys_prompt, user_prompt, signiture):
        sha1_hash = self._generate_sha1(user_prompt)

        # Check if file is in cache
        if self.file_path in self.cache:
            # Check if the user prompt's SHA1 is in the self.cache for this file
            for entry in self.cache[self.file_path]:
                if entry["sha1"] == sha1_hash:
                    # Update last_accessed timestamp
                    entry["last_accessed"] = self._get_current_timestamp()
                    # Return cached docstring if found
                    return entry["docstring"]

        print("    Requesting AI for: " + signiture)
        # If no self.cache hit, call the AI and get the docstring
        res = self.ai.improve_text(sys_prompt, user_prompt)

        # Create a new self.cache entry with last_accessed timestamp
        new_entry = {
            "sha1": sha1_hash,
            "docstring": res,
            "last_accessed": self._get_current_timestamp(),
        }

        # Add new entry to the self.cache for the current file
        if self.file_path not in self.cache:
            self.cache[self.file_path] = []

        self.cache[self.file_path].append(new_entry)

        # Return the new docstring from AI
        return res

    def remove_old_entries(self, minutes):
        current_timestamp = self._get_current_timestamp()
        threshold_timestamp = current_timestamp - (minutes * 60)

        # Remove old entries for each file in the self.cache
        for file_path, entries in self.cache.items():
            self.cache[file_path] = [
                entry
                for entry in entries
                if "last_accessed" in entry
                and entry["last_accessed"] >= threshold_timestamp
            ]

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
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write(
                "".join(self.lines).encode()
            )  # Write the content to the temporary file

        try:
            # Attempt to compile the temporary file
            result = subprocess.run(
                ["python", "-m", "py_compile", temp_file_path],
                capture_output=True,
                text=True,
            )

            # If there is no compilation error (i.e., result.returncode == 0), move the file to the destination
            if result.returncode == 0:
                with open(self.file_path, "w") as file:
                    print(f"    Wrote: {self.file_path}")
                    file.write("".join(self.lines))  # Write to the destination file
            else:
                print(f"    Error compiling file: {result.stderr}")
                if self.debug:
                    name = "/tmp/" + os.path.basename(self.file_path) + ".failed"
                    with open(name, "w") as file:
                        file.write("".join(self.lines))
                        print(f"    Copied here: {name}")
                        if self.exit:
                            sys.exit(1)

        finally:
            # Clean up the temporary file
            os.remove(temp_file_path)

        self.remove_old_entries(1440 * 14)
        self._save_cache()

    def generate_class_docstring(self):
        line = self.lines[self.line_index]
        class_definition = line
        output = re.sub("\\s+", " ", class_definition.rstrip().replace("\n", " "))
        print("   -> " + output)
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
            system_prompt_class, "\n".join(prompt_class_code), output
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

        # self.print_debug("class docstring: " + class_definition.strip(), self.lines)

        return True

    def generate_function_docstring(self):
        line = self.lines[self.line_index]
        mutliline_line = ""

        if not (
            line.strip().endswith("):")
            and not re.search(r"\)\s*->\s*(.*)\s*:.*", line.strip())
        ):
            self.multiline_index = 0
            # multiline def signiture
            while self.line_index < len(self.lines):
                mutliline_line += self.lines[self.line_index]
                if re.match(
                    r".*\):$", self.lines[self.line_index].strip()
                ) or re.search(
                    r".*\)\s*->\s*(.*)\s*:.*", self.lines[self.line_index].strip()
                ):
                    break
                self.line_index += 1
                self.multiline_index += 1

        def_definition = line if mutliline_line == "" else mutliline_line
        output = re.sub("\\s+", " ", def_definition.rstrip().replace("\n", " "))
        print("     -> " + output)
        prompt_def_code = (
            mutliline_line.split("\n") if mutliline_line != "" else [def_definition]
        )

        indent_line = self.count_and_divide_whitespace(
            def_definition if mutliline_line == "" else mutliline_line.splitlines()[0]
        )
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
        indent = (
            self.count_and_divide_whitespace(
                def_definition
                if mutliline_line == ""
                else mutliline_line.splitlines()[0]
            )
            + 1
        )
        def_docstring = self.get_ai_docstring(
            system_prompt_def, "\n".join(prompt_def_code), output
        )
        def_docstring = self.wrap_text(def_docstring, max_length=120, indent=indent)
        def_docstring[len(def_docstring) - 1] = (
            def_docstring[len(def_docstring) - 1] + "\n"
        )
        if def_definition.strip() == def_docstring[0].strip():
            def_docstring = def_docstring[
                1 if mutliline_line == "" else self.multiline_index :
            ]
        def_docstring = [line + "\n" for line in def_docstring]
        def_docstring[len(def_docstring) - 1] = (
            def_docstring[len(def_docstring) - 1].rstrip() + "\n"
        )

        # Handle one-liner docstring or multi-line docstring
        if '"""' in self.lines[self.line_index + 1]:
            stripped_line = self.lines[self.line_index + 1].strip()
            if re.match(r'"""[\s\S]+?"""', stripped_line):
                # This is a one-liner or multi-line docstring (we always replace with a multi-line docstring)
                self.lines = (
                    self.lines[: self.line_index + 1]
                    + def_docstring
                    + self.lines[self.line_index + 2 :]
                )
            else:
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

        # self.print_debug("def docstring: " + def_definition.strip(), self.lines)

        self.line_index = self.line_index + len(def_docstring)
        return True

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
            system_prompt_general, "".join(self.lines), self.file_path
        )
        general_description = self.wrap_text(
            general_description, max_length=120, indent=0
        )
        docstring = [line + "\n" for line in general_description]

        # self.print_debug("docstring_end_index", str(docstring_end_index))
        # self.print_debug("self.lines[:docstring_start_index]", self.lines[:docstring_start_index])
        # self.print_debug("docstring", docstring)
        # self.print_debug("self.lines[docstring_end_index + 1 :]", self.lines[docstring_end_index + 1 :])

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

        # self.print_debug("file docstring: " + self.file_path, self.lines)

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


def process_file(file_path, debug=False, exit=False):
    """Process a single file by generating docstrings."""
    Docstring(file_path, debug=debug, exit=exit).generate_docstrings()


def process_directory(directory_path, recursive=False, debug=False, exit=False):
    """Process all Python files in the directory with progress tracking."""

    # List all python files
    python_files = [
        os.path.join(root, file)
        for root, dirs, files in os.walk(directory_path)
        for file in files
        if file.endswith(".py")
    ]

    total_files = len(python_files)  # Total python files count
    processed_files = 0

    print(f"Processing {total_files} Python files...")

    for file_path in python_files:
        process_file(file_path, debug=debug, exit=exit)
        processed_files += 1
        print(f"\nProcessing file: {processed_files}/{total_files}")

        # If we don't want recursive traversal, we break the loop once we're done with this level
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
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Copies failed updates to /tmp/",
    )
    parser.add_argument(
        "-e",
        "--exit",
        action="store_true",
        help="Exits on failure",
    )
    # Parse the arguments
    args = parser.parse_args()

    # Check if the path is a file or directory
    if os.path.isfile(args.path):
        # If it's a file, process it directly
        process_file(args.path, debug=args.debug, exit=args.exit)
    elif os.path.isdir(args.path):
        # If it's a directory, process all Python files
        process_directory(
            args.path, recursive=args.recursive, debug=args.debug, exit=args.exit
        )
    else:
        print(f"Error: {args.path} is neither a valid file nor a directory.")

    OpenAICost.print_cost_metrics()


if __name__ == "__main__":
    main()
