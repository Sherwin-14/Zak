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


class GitHubNotFoundError(GitHubError):
    """Raised when the owner, repo, or issue cannot be resolved."""


class LLMError(HekmoError):
    """Base exception for LLM API failures (currently DeepSeek; provider-agnostic)."""


class LLMAuthError(LLMError):
    """Raised on 401 — expired or invalid API key for the configured LLM provider."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM API request times out."""


class LLMConnectionError(LLMError):
    """Raised when the LLM provider is unreachable (DNS, connection refused, etc.)."""


class TemplateError(HekmoError):
    """Raised when templates.json or system_prompt.md is missing or malformed."""
