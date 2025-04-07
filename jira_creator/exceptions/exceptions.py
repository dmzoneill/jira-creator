# exceptions/jira_exceptions.py


class BaseException(Exception):
    """Base class for all Jira-related exceptions."""

    pass


class MissingConfigVariable(BaseException):
    """Exception raised when a required Jira environment variable is missing."""

    pass
