# exceptions/jira_exceptions.py


class BaseException(Exception):
    """Base class for all Jira-related exceptions."""

    pass


class MissingConfigVariable(BaseException):
    """Exception raised when a required Jira environment variable is missing."""

    pass


class SetStoryEpicError(BaseException):
    pass


class ListIssuesError(BaseException):
    pass


class SetAcceptanceCriteriaError(BaseException):
    pass


class DispatcherError(BaseException):
    pass


class EditIssueError(BaseException):
    pass


class FetchDescriptionError(BaseException):
    pass


class EditDescriptionError(BaseException):
    pass


class RemoveFromSprintError(BaseException):
    pass


class ChangeIssueTypeError(BaseException):
    pass


class UnassignIssueError(BaseException):
    pass


class AssignIssueError(BaseException):
    pass


class FetchIssueIDError(BaseException):
    pass


class VoteStoryPointsError(BaseException):
    pass


class GetPromptError(BaseException):
    pass


class UpdateDescriptionError(BaseException):
    pass


class MigrateError(BaseException):
    pass


class OpenIssueError(BaseException):
    pass


class ViewIssueError(BaseException):
    pass


class AddSprintError(BaseException):
    pass


class SetStatusError(BaseException):
    pass


class BlockError(BaseException):
    pass


class UnBlockError(BaseException):
    pass


class AddCommentError(BaseException):
    pass


class AiError(BaseException):
    pass


class SearchError(BaseException):
    pass


class CreateIssueError(BaseException):
    pass


class LintAllError(BaseException):
    pass


class LintError(BaseException):
    pass


class SetPriorityError(BaseException):
    pass


class SetStoryPointsError(BaseException):
    pass


class ChangeTypeError(BaseException):
    pass


class ListBlockedError(BaseException):
    pass


class InvalidPromptError(BaseException):
    pass


class JiraClientRequestError(BaseException):
    pass


class QuarterlyConnectionError(BaseException):
    pass


class GTP4AllError(BaseException):
    pass


class AiProviderError(BaseException):
    pass


class AIHelperError(BaseException):
    pass


class GetUserError(BaseException):
    pass


class SearchUsersError(BaseException):
    pass
