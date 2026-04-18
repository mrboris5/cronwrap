import subprocess
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    command: str
    returncode: int
    stdout: str
    stderr: str
    duration: float
    attempt: int = 1

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_command(
    command: str,
    timeout: Optional[int] = None,
    retries: int = 0,
    retry_delay: float = 5.0,
) -> RunResult:
    """Run a shell command with optional retries and timeout."""
    last_result = None

    for attempt in range(1, retries + 2):
        logger.debug("Running command (attempt %d): %s", attempt, command)
        start = time.monotonic()

        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.monotonic() - start
            last_result = RunResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                duration=duration,
                attempt=attempt,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            logger.warning("Command timed out after %ss", timeout)
            last_result = RunResult(
                command=command,
                returncode=-1,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                duration=duration,
                attempt=attempt,
            )

        if last_result.success:
            logger.debug("Command succeeded on attempt %d", attempt)
            return last_result

        if attempt <= retries:
            logger.info("Retrying in %.1fs (attempt %d/%d)", retry_delay, attempt, retries + 1)
            time.sleep(retry_delay)

    return last_result
