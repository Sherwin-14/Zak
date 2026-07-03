"""Custom exceptions for hekmo, each carrying a user-facing message and hint."""


class HekmoError(Exception):
    """Base exception for all hekmo errors, with a display message and hint."""

    def __init__(self, message: str, hint: str | None = None):
        self.message = message
        self.hint = hint
        super().__init__(message)


class ConfigError(HekmoError):
    """Raised when required config (tokens, templates, etc.) is missing or invalid."""


class TokenMissingError(ConfigError):
    """Raised when a required API token/key is not set in the environment."""


class GitHubError(HekmoError):
    """Base exception for GitHub API failures."""


class GitHubAuthError(GitHubError):
    """Raised on 401 — expired or invalid GitHub token."""


class GitHubNotFoundError(GitHubError):
    """Raised when the owner, repo, or issue cannot be resolved."""


class GitHubTimeoutError(GitHubError):
    """Raised when the GitHub API request times out."""


class GitHubConnectionError(GitHubError):
    """Raised when GitHub is unreachable (DNS, connection refused, etc.)."""


class DeepSeekError(HekmoError):
    """Base exception for DeepSeek/LLM API failures."""


class DeepSeekAuthError(DeepSeekError):
    """Raised on 401 — expired or invalid DeepSeek API key."""


class DeepSeekTimeoutError(DeepSeekError):
    """Raised when the DeepSeek API request times out."""


class DeepSeekConnectionError(DeepSeekError):
    """Raised when DeepSeek is unreachable (DNS, connection refused, etc.)."""


class TemplateError(HekmoError):
    """Raised when templates.json or system_prompt.md is missing or malformed."""
