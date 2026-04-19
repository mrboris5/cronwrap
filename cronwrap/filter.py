"""Output filtering: truncate, redact secrets, and summarize command output."""

import re
from typing import List, Optional

DEFAULT_MAX_LINES = 200
DEFAULT_MAX_BYTES = 64 * 1024  # 64 KB

_SECRET_PATTERNS = [
    re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key)\s*[=:]\s*\S+'),
]


def redact(text: str, patterns: Optional[List[re.Pattern]] = None) -> str:
    """Replace secret-looking values with [REDACTED]."""
    if patterns is None:
        patterns = _SECRET_PATTERNS
    for pat in patterns:
        text = pat.sub(lambda m: m.group(0).split(m.group(0)[-len(m.group(0).split()[-1]):])[0] + '[REDACTED]', text)
        # simpler replacement
        text = pat.sub(lambda m: re.sub(r'([=:]\s*)\S+', r'\1[REDACTED]', m.group(0)), text)
    return text


def truncate_lines(text: str, max_lines: int = DEFAULT_MAX_LINES) -> str:
    """Keep only the last max_lines lines, prepending a notice if truncated."""
    lines = text.splitlines(keepends=True)
    if len(lines) <= max_lines:
        return text
    dropped = len(lines) - max_lines
    kept = lines[-max_lines:]
    return f"[... {dropped} lines truncated ...]\n" + "".join(kept)


def truncate_bytes(text: str, max_bytes: int = DEFAULT_MAX_BYTES) -> str:
    """Truncate text to at most max_bytes UTF-8 bytes."""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + "\n[... output truncated ...]"


def filter_output(
    text: str,
    max_lines: int = DEFAULT_MAX_LINES,
    max_bytes: int = DEFAULT_MAX_BYTES,
    redact_secrets: bool = True,
) -> str:
    """Apply all filters to command output."""
    if redact_secrets:
        text = redact(text)
    text = truncate_lines(text, max_lines)
    text = truncate_bytes(text, max_bytes)
    return text
