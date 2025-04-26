#!/usr/bin/env python
"""
This module defines a collection of custom exceptions for handling various error scenarios encountered during
interactions with Jira. Each exception class extends the BaseException class and targets specific issues such as
missing configuration variables, errors in setting story epics, listing and editing issues, managing descriptions,
assigning/unassigning issues, voting on story points, and other Jira-related operations. The structured approach
to exception handling allows for clearer error management and debugging in applications that integrate with Jira.
"""


class MissingConfigVariable(BaseException):
    """Represents an exception raised when a required Jira environment variable is missing."""


class SetStoryEpicError(BaseException):
    """This class represents a custom exception for errors related to setting a story epic."""


class ListIssuesError(BaseException):
    """This class represents a custom exception called ListIssuesError."""


class SetAcceptanceCriteriaError(BaseException):
    """This class represents a custom exception for errors related to setting acceptance criteria."""


class DispatcherError(BaseException):
    """This class represents a custom exception called DispatcherError."""


class EditIssueError(BaseException):
    """This class represents a custom exception for errors that occur while trying to edit an issue."""


class FetchDescriptionError(BaseException):
    """This class represents a custom exception for errors that occur during fetching descriptions."""


class EditDescriptionError(BaseException):
    """This class represents a custom exception for errors related to editing descriptions."""


class RemoveFromSprintError(BaseException):
    """A custom exception class for handling errors related to removing items from a sprint."""


class ChangeIssueTypeError(BaseException):
    """This class represents an exception raised when attempting to change the type of an issue."""


class UnassignIssueError(BaseException):
    """This class represents an error that occurs when trying to unassign an issue that is not assigned to anyone."""


class AssignIssueError(BaseException):
    """This class represents an error that occurs when trying to assign an issue."""


class FetchIssueIDError(BaseException):
    """This class represents a custom exception called FetchIssueIDError."""


class VoteStoryPointsError(BaseException):
    """This class represents a custom exception for errors related to voting story points."""


class GetPromptError(BaseException):
    """This class represents an exception raised when there is an error in retrieving a prompt."""


class UpdateDescriptionError(BaseException):
    """This class represents an exception that is raised when an error occurs while updating a description."""


class MigrateError(BaseException):
    """This class represents a custom exception for migration errors."""


class OpenIssueError(BaseException):
    """This class represents an exception for an open issue."""


class ViewIssueError(BaseException):
    """This class represents an error that occurs when viewing an issue fails."""


class AddSprintError(BaseException):
    """This class represents an error that occurs when attempting to add a sprint to a project."""


class SetStatusError(BaseException):
    """This class represents a custom exception called SetStatusError."""


class BlockError(BaseException):
    """A custom exception class for handling errors related to blocks in a program."""


class UnBlockError(BaseException):
    """This class represents a custom exception called UnBlockError."""


class AddCommentError(BaseException):
    """This class represents an error that occurs when attempting to add a comment."""


class AiError(BaseException):
    """This class represents a custom exception for AI-related errors."""


class SearchError(BaseException):
    """This class represents a custom exception for search-related errors."""


class CreateIssueError(BaseException):
    """This class represents an error that occurs when creating an issue."""


class LintAllError(BaseException):
    """A custom exception class representing an error that occurred during linting all files."""


class LintError(BaseException):
    """This class represents a custom exception for linting errors."""


class SetPriorityError(BaseException):
    """This class represents a custom exception called SetPriorityError."""


class SetStoryPointsError(BaseException):
    """
    This class represents an error that occurs when trying to
    set story points for a task in a project management system.
    """


class ChangeTypeError(BaseException):
    """This class represents a custom exception for handling type errors during a change operation."""


class ListBlockedError(BaseException):
    """This class represents an exception for when a list is blocked from performing an operation."""


class InvalidPromptError(BaseException):
    """This class represents an exception for invalid prompts."""


class JiraClientRequestError(BaseException):
    """This class represents an exception raised when there is an error in making a request to the Jira client."""


class QuarterlyConnectionError(BaseException):
    """This class represents a custom exception for handling connection errors that occur on a quarterly basis."""


class GTP4AllError(BaseException):
    """This class represents a custom error called GTP4AllError that inherits from BaseException."""


class AiProviderError(BaseException):
    """This class represents an error specific to an AI provider."""


class AIHelperError(BaseException):
    """This class represents a custom exception for errors that occur in an AI helper application."""


class GetUserError(BaseException):
    """This class represents a custom exception called GetUserError that can be raised in specific situations."""


class SearchUsersError(BaseException):
    """This class represents an error that occurs during user search operations."""


class RemoveFlagError(BaseException):
    """This class represents a custom exception for flag removal errors."""
