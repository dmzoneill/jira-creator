"""
This module defines a variety of custom exceptions related to Jira operations. Each exception represents a specific
error scenario that may occur during Jira interactions. These exceptions are derived from the BaseException class and
provide detailed error handling for different situations such as missing configuration variables, errors in setting
story epic, listing issues, editing issues, fetching descriptions, assigning/unassigning issues, voting story points,
updating descriptions, migrating, opening/viewing issues, adding comments, and various other Jira-related operations.
"""

# exceptions/jira_exceptions.py


class BaseException(Exception):
    """
    Base class for all Jira-related exceptions.
    """

    pass


class MissingConfigVariable(BaseException):
    """
    Represents an exception raised when a required Jira environment variable is missing.

    Attributes:
    BaseException: The base exception class in Python.
    """

    pass


class SetStoryEpicError(BaseException):
    """
    This class represents a custom exception for errors related to setting a story epic.

    Attributes:
    No specific attributes are defined in this class.
    """

    pass


class ListIssuesError(BaseException):
    """
    This class represents a custom exception called ListIssuesError.

    Attributes:
    None
    """

    pass


class SetAcceptanceCriteriaError(BaseException):
    """
    This class represents a custom exception for errors related to setting acceptance criteria.

    Attributes:
    None
    """

    pass


class DispatcherError(BaseException):
    """
    This class represents a custom exception called DispatcherError.

    Attributes:
    - None
    """

    pass


class EditIssueError(BaseException):
    """
    This class represents a custom exception for errors that occur while trying to edit an issue.

    Attributes:
    None
    """

    pass


class FetchDescriptionError(BaseException):
    """
    This class represents a custom exception for errors that occur during fetching descriptions.

    Attributes:
    None
    """

    pass


class EditDescriptionError(BaseException):
    """
    This class represents a custom exception for errors related to editing descriptions.

    Attributes:
    None
    """

    pass


class RemoveFromSprintError(BaseException):
    """
    A custom exception class for handling errors related to removing items from a sprint.

    Attributes:
    None
    """

    pass


class ChangeIssueTypeError(BaseException):
    """
    This class represents an exception raised when attempting to change the type of an issue.

    Attributes:
    No attributes are defined for this class.
    """

    pass


class UnassignIssueError(BaseException):
    """
    This class represents an error that occurs when trying to unassign an issue that is not assigned to anyone.

    Attributes:
    None
    """

    pass


class AssignIssueError(BaseException):
    """
    This class represents an error that occurs when trying to assign an issue.

    Attributes:
    None
    """

    pass


class FetchIssueIDError(BaseException):
    """
    This class represents a custom exception called FetchIssueIDError.

    Attributes:
    None
    """

    pass


class VoteStoryPointsError(BaseException):
    """
    This class represents a custom exception for errors related to voting story points.

    Attributes:
    None
    """

    pass


class GetPromptError(BaseException):
    """
    This class represents an exception raised when there is an error in retrieving a prompt.

    Attributes:
    No attributes are defined explicitly in this class.
    """

    pass


class UpdateDescriptionError(BaseException):
    """
    This class represents an exception that is raised when an error occurs while updating a description.

    Attributes:
    None
    """

    pass


class MigrateError(BaseException):
    """
    This class represents a custom exception for migration errors.

    Attributes:
    None
    """

    pass


class OpenIssueError(BaseException):
    """
    This class represents an exception for an open issue.

    Attributes:
    None
    """

    pass


class ViewIssueError(BaseException):
    """
    This class represents an error that occurs when viewing an issue fails.

    Attributes:
    None
    """

    pass


class AddSprintError(BaseException):
    """
    This class represents an error that occurs when attempting to add a sprint to a project.

    Attributes:
    None
    """

    pass


class SetStatusError(BaseException):
    """
    This class represents a custom exception called SetStatusError.

    Attributes:
    - None
    """

    pass


class BlockError(BaseException):
    """
    A custom exception class for handling errors related to blocks in a program.

    Attributes:
    No specific attributes defined.
    """

    pass


class UnBlockError(BaseException):
    """
    This class represents a custom exception called UnBlockError.

    Attributes:
    - No specific attributes defined.
    """

    pass


class AddCommentError(BaseException):
    """
    This class represents an error that occurs when attempting to add a comment.

    Attributes:
    No specific attributes are defined in this class.
    """

    pass


class AiError(BaseException):
    """
    This class represents a custom exception for AI-related errors.

    Attributes:
    None
    """

    pass


class SearchError(BaseException):
    """
    This class represents a custom exception for search-related errors.

    Attributes:
    None
    """

    pass


class CreateIssueError(BaseException):
    """
    This class represents an error that occurs when creating an issue.

    Attributes:
    None
    """

    pass


class LintAllError(BaseException):
    """
    A custom exception class representing an error that occurred during linting all files.

    Attributes:
    None
    """

    pass


class LintError(BaseException):
    """
    This class represents a custom exception for linting errors.

    Attributes:
    No specific attributes.
    """

    pass


class SetPriorityError(BaseException):
    """
    This class represents a custom exception called SetPriorityError.

    Attributes:
    - None
    """

    pass


class SetStoryPointsError(BaseException):
    """
    This class represents an error that occurs when trying to set story points for a task in a project management
    system.

    Attributes:
    No specific attributes are defined for this class.
    """

    pass


class ChangeTypeError(BaseException):
    """
    This class represents a custom exception for handling type errors during a change operation.

    Attributes:
    None
    """

    pass


class ListBlockedError(BaseException):
    """
    This class represents an exception for when a list is blocked from performing an operation.

    Attributes:
    No attributes defined.
    """

    pass


class InvalidPromptError(BaseException):
    """
    This class represents an exception for invalid prompts.

    Attributes:
    No specific attributes.
    """

    pass


class JiraClientRequestError(BaseException):
    """
    This class represents an exception raised when there is an error in making a request to the Jira client.

    Attributes:
    None
    """

    pass


class QuarterlyConnectionError(BaseException):
    """
    This class represents a custom exception for handling connection errors that occur on a quarterly basis.

    Attributes:
    None
    """

    pass


class GTP4AllError(BaseException):
    """
    This class represents a custom error called GTP4AllError that inherits from BaseException.
    It is used to handle specific exceptions related to the GTP4All system.
    """

    pass


class AiProviderError(BaseException):
    """
    This class represents an error specific to an AI provider.

    Attributes:
    No specific attributes.
    """

    pass


class AIHelperError(BaseException):
    """
    This class represents a custom exception for errors that occur in an AI helper application.

    Attributes:
    None
    """

    pass


class GetUserError(BaseException):
    """
    This class represents a custom exception called GetUserError that can be raised in specific situations.
    Attributes:
    - None
    """

    pass


class SearchUsersError(BaseException):
    """
    This class represents an error that occurs during user search operations.

    Attributes:
    None
    """

    pass


class RemoveFlagError(BaseException):
    """
    This class represents a custom exception for flag removal errors.

    Attributes:
    No attributes are defined for this class.
    """

    pass
