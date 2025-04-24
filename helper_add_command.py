import os
import sys


# Define a function to format the command name into a subcommand-friendly format
def format_command_name(command_name):
    # Replace underscores with hyphens and convert to lowercase
    return command_name.replace("_", "-").lower()


# Function to create the necessary files based on the command name
def create_files(command_name):
    # Format the command name to be used in the subparser and other places
    formatted_command = format_command_name(command_name)

    # Define the paths and contents for new files based on the formatted command name
    command_file_content = f"""def cli_{command_name}(jira, args):
    flag_name = args.flag_name
    issue_key = args.issue_key
    response = jira.add_flag_to_issue(issue_key, flag_name)
    return response
"""

    init_content = f"""from .cli_{command_name} import cli_{command_name}  # noqa\n"""

    rh_jira_update_method = f"""    def {command_name}(self, args: Namespace) -> None:
        return cli_{command_name}(self.jira, args)
"""

    subcommand_update = f"""{command_name} = add("{formatted_command}", "Add a flag to a specific issue")
        {command_name}.add_argument("issue_key", help="The key of the issue")
        {command_name}.add_argument("flag_name", help="The name of the flag to add")
"""

    rest_op_file_content = f"""def {command_name}(request_fn, issue_key, flag_name) -> dict:
    path = f"/rest/api/2/issue/{{issue_key}}/flags"
    payload = {{"flag": flag_name}}
    return request_fn("POST", path, json=payload)
"""

    jira_client_update = f"""\n    def {command_name}(self, issue_key, flag_name):
        return {command_name}(self._request, issue_key, flag_name)
"""

    # Function to append content to a file if it doesn't exist
    def append_to_file(file_path, content):
        with open(file_path, "a") as f:
            f.write(content)

    # Function to add cli_add_flag above "# commands entry" in rh_jira.py
    def update_rh_jira_imports():
        with open("jira_creator/rh_jira.py", "r") as f:
            content = f.readlines()

        # Find the line with "# commands entry" and add cli_add_flag above it
        for i, line in enumerate(content):
            if "# commands entry" in line:
                # Insert cli_add_flag above the "# commands entry" line
                content.insert(i, f"    cli_{command_name},\n")
                break

        # Write back the updated content to rh_jira.py
        with open("jira_creator/rh_jira.py", "w") as f:
            f.writelines(content)

    # Function to add "add_flag" above "# commands entry" in client.py
    def update_client_imports():
        with open("jira_creator/rest/client.py", "r") as f:
            content = f.readlines()

        # Find the line with "# commands entry" and add "add_flag" above it
        for i, line in enumerate(content):
            if "# commands entry" in line:
                # Insert "add_flag" above the "# commands entry" line
                content.insert(i, f"    {command_name},\n")
                break

        # Write back the updated content to client.py
        with open("jira_creator/rest/client.py", "w") as f:
            f.writelines(content)

    # Function to insert rh_jira_update_method after "# add new df here" in rh_jira.py
    def insert_rh_jira_update_method():
        with open("jira_creator/rh_jira.py", "r") as f:
            content = f.readlines()

        # Find the line with "# add new df here" and insert rh_jira_update_method after it
        for i, line in enumerate(content):
            if "# add new df here" in line:
                # Insert rh_jira_update_method after the "# add new df here" line
                content.insert(i, rh_jira_update_method + "\n\n")
                break

        # Write back the updated content to rh_jira.py
        with open("jira_creator/rh_jira.py", "w") as f:
            f.writelines(content)

    # Create necessary files and directories
    os.makedirs("jira_creator/commands", exist_ok=True)
    with open(f"jira_creator/commands/cli_{command_name}.py", "w") as f:
        f.write(command_file_content)

    # Append to __init__.py in the commands directory
    append_to_file("jira_creator/commands/__init__.py", init_content)

    # Update the imports in rh_jira.py
    update_rh_jira_imports()

    # Update the _register_subcommands method in rh_jira.py with the corrected subcommand_update
    with open("jira_creator/rh_jira.py", "r") as f:
        content = f.read()

    content = content.replace(
        "# Add your other subcommands here",
        subcommand_update + "\n        # Add your other subcommands here\n",
    )

    with open("jira_creator/rh_jira.py", "w") as f:
        f.write(content)

    # Insert the method after "# add new df here"
    insert_rh_jira_update_method()

    # Rest operation file
    os.makedirs("jira_creator/rest/ops", exist_ok=True)
    with open(f"jira_creator/rest/ops/{command_name}.py", "w") as f:
        f.write(rest_op_file_content)

    # Append update to the __init__.py in rest/ops
    append_to_file(
        "jira_creator/rest/ops/__init__.py",
        f"from .{command_name} import {command_name}  # noqa\n",
    )

    # Jira client update
    append_to_file("jira_creator/rest/client.py", jira_client_update)

    # Update the imports in client.py
    update_client_imports()

    print(f"Files created and updated successfully for command: {command_name}")


# Entry point of the script
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python add_flag_command_setup.py <command_name>")
        sys.exit(1)

    command_name = sys.argv[1]
    create_files(command_name)
