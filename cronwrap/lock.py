"""File-based locking to prevent concurrent cron job execution."""

import os
import time
from pathlib import Path


class LockError(Exception):
    """Raised when a lock cannot be acquired."""


class JobLock:
    def __init__(self, lock_dir: str, job_name: str, timeout: int = 0):
        self.lock_dir = Path(lock_dir)
        self.job_name = job_name
        self.timeout = timeout
        self.lock_file = self.lock_dir / f"{job_name}.lock"
        self._acquired = False

    def acquire(self) -> None:
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self._acquired = True
                return
            except FileExistsError:
                if time.monotonic() >= deadline:
                    raise LockError(
                        f"Could not acquire lock for '{self.job_name}' "
                        f"(lock file: {self.lock_file})"
                    )
                time.sleep(0.5)

    def release(self) -> None:
        if self._acquired and self.lock_file.exists():
            self.lock_file.unlink()
            self._acquired = False

    def __enter__(self) -> "JobLock":
        self.acquire()
        return self

    def __exit__(self, *args) -> None:
        self.release()

    @property
    def is_locked(self) -> bool:
        return self.lock_file.exists()
