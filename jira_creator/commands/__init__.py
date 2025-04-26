#!/usr/bin/env python
"""
This file includes multiple CLI commands for managing issues and users in a project management system. Each CLI command
is imported from a corresponding module in the package. The CLI commands cover various functionalities such as adding
comments, flags, sprints, assigning tasks, editing issues, linting, listing issues and sprints, searching, setting
criteria, priorities, status, story details, talking, unassigning, unblocking, validating, viewing, and voting on story
points. These commands provide a comprehensive set of tools for interacting with the project management system via the
command line interface.
"""

from typing import Callable

CliCommand: Callable[..., None]

from ._try_cleanup import _try_cleanup  # type: ignore
from .cli_add_comment import cli_add_comment  # type: ignore
from .cli_add_flag import cli_add_flag  # type: ignore
from .cli_add_to_sprint import cli_add_to_sprint  # type: ignore
from .cli_ai_helper import cli_ai_helper  # type: ignore
from .cli_assign import cli_assign  # type: ignore
from .cli_block import cli_block  # type: ignore
from .cli_blocked import cli_blocked  # type: ignore
from .cli_change_type import cli_change_type  # type: ignore
from .cli_clone_issue import cli_clone_issue  # type: ignore
from .cli_create_issue import cli_create_issue  # type: ignore
from .cli_edit_issue import cli_edit_issue  # type: ignore
from .cli_get_sprint import cli_get_sprint  # type: ignore
from .cli_lint import cli_lint  # type: ignore
from .cli_lint_all import cli_lint_all  # type: ignore
from .cli_list_issues import cli_list_issues  # type: ignore
from .cli_list_sprints import cli_list_sprints  # type: ignore
from .cli_migrate import cli_migrate  # type: ignore
from .cli_open_issue import cli_open_issue  # type: ignore
from .cli_quarterly_connection import cli_quarterly_connection  # type: ignore
from .cli_remove_flag import cli_remove_flag  # type: ignore
from .cli_remove_sprint import cli_remove_sprint  # type: ignore
from .cli_search import cli_search  # type: ignore
from .cli_search_users import cli_search_users  # type: ignore
from .cli_set_acceptance_criteria import cli_set_acceptance_criteria  # type: ignore
from .cli_set_priority import cli_set_priority  # type: ignore
from .cli_set_status import cli_set_status  # type: ignore
from .cli_set_story_epic import cli_set_story_epic  # type: ignore
from .cli_set_story_points import cli_set_story_points  # type: ignore
from .cli_set_summary import cli_set_summary  # type: ignore
from .cli_talk import cli_talk  # type: ignore
from .cli_unassign import cli_unassign  # type: ignore
from .cli_unblock import cli_unblock  # type: ignore
from .cli_validate_issue import cli_validate_issue  # type: ignore
from .cli_view_issue import cli_view_issue  # type: ignore
from .cli_view_user import cli_view_user  # type: ignore
from .cli_vote_story_points import cli_vote_story_points  # type: ignore