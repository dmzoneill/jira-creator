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

from ._try_cleanup import _try_cleanup  # noqa
from .cli_add_comment import cli_add_comment  # noqa
from .cli_add_flag import cli_add_flag  # noqa
from .cli_add_to_sprint import cli_add_to_sprint  # noqa
from .cli_ai_helper import cli_ai_helper  # noqa
from .cli_assign import cli_assign  # noqa
from .cli_block import cli_block  # noqa
from .cli_blocked import cli_blocked  # noqa
from .cli_change_type import cli_change_type  # noqa
from .cli_clone_issue import cli_clone_issue  # noqa
from .cli_create_issue import cli_create_issue  # noqa
from .cli_edit_issue import cli_edit_issue  # noqa
from .cli_get_sprint import cli_get_sprint  # noqa
from .cli_lint import cli_lint  # noqa
from .cli_lint_all import cli_lint_all  # noqa
from .cli_list_issues import cli_list_issues  # noqa
from .cli_list_sprints import cli_list_sprints  # noqa
from .cli_migrate import cli_migrate  # noqa
from .cli_open_issue import cli_open_issue  # noqa
from .cli_quarterly_connection import cli_quarterly_connection  # noqa
from .cli_remove_flag import cli_remove_flag  # noqa
from .cli_remove_sprint import cli_remove_sprint  # noqa
from .cli_search import cli_search  # noqa
from .cli_search_users import cli_search_users  # noqa
from .cli_set_acceptance_criteria import cli_set_acceptance_criteria  # noqa
from .cli_set_priority import cli_set_priority  # noqa
from .cli_set_status import cli_set_status  # noqa
from .cli_set_story_epic import cli_set_story_epic  # noqa
from .cli_set_story_points import cli_set_story_points  # noqa
from .cli_set_summary import cli_set_summary  # noqa
from .cli_talk import cli_talk  # noqa
from .cli_unassign import cli_unassign  # noqa
from .cli_unblock import cli_unblock  # noqa
from .cli_validate_issue import cli_validate_issue  # noqa
from .cli_view_issue import cli_view_issue  # noqa
from .cli_view_user import cli_view_user  # noqa
from .cli_vote_story_points import cli_vote_story_points  # noqa

CliCommand: Callable[..., None]
