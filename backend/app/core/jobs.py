"""
backend/app/core/jobs.py
========================
In-process background job system with lifecycle tracking, bounded retries,
exponential backoff, and non-retryable failure filtering.
"""

from __future__ import annotations

import asyncio
import datetime
import traceback
from typing import Any, Callable, Dict, List, Optional
import uuid

from backend.app.core.logging import get_logger

logger = get_logger("floody.jobs")

NON_RETRYABLE_ERRORS = {
    "AUTH_FORBIDDEN",
    "AUTH_INVALID",
    "VALIDATION_ERROR",
    "TELEMETRY_INTEGRITY_VIOLATION",
    "TELEMETRY_INVALID_TIMESTAMP",
    "TELEMETRY_FUTURE_TIMESTAMP",
    "ALERT_NOT_AUTHORIZED",
    "ALERT_INVALID_STATE",
}


class BackgroundJob:
    def __init__(
        self,
        job_type: str = "GENERIC_TASK",
        func: Optional[Callable[..., Any]] = None,
        args: Optional[tuple] = None,
        kwargs: Optional[dict] = None,
        max_retries: int = 3,
        correlation_id: Optional[str] = None,
        job_id: Optional[str] = None,
        initial_delay_sec: float = 0.5,
    ):
        self.job_id = job_id or str(uuid.uuid4())
        self.job_type = job_type
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.max_retries = max_retries
        self.attempt = 0
        self.initial_delay_sec = initial_delay_sec
        self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.started_at: Optional[datetime.datetime] = None
        self.completed_at: Optional[datetime.datetime] = None
        self.status = "QUEUED"  # QUEUED, RUNNING, SUCCESS, FAILED, RETRYING, CANCELLED
        self.error: Optional[str] = None
        self.result: Any = None
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self._last_exception: Optional[Exception] = None

    @property
    def attempts(self) -> int:
        return self.attempt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "status": self.status,
            "attempt": self.attempt,
            "attempts": self.attempt,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "correlation_id": self.correlation_id,
        }


class JobManager:
    """Manages asynchronous operational jobs and execution status."""

    def __init__(self):
        self._jobs: Dict[str, BackgroundJob] = {}

    def enqueue(
        self,
        job_type: str,
        func: Callable[..., Any],
        *args: Any,
        max_retries: int = 3,
        correlation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> BackgroundJob:
        job = BackgroundJob(
            job_type=job_type,
            func=func,
            args=args,
            kwargs=kwargs,
            max_retries=max_retries,
            correlation_id=correlation_id,
        )
        self._jobs[job.job_id] = job
        # Launch background execution
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._run_job(job))
        except RuntimeError:
            # Synchronous / test fallback
            self._execute_sync(job)
        return job

    def execute_sync(self, job: BackgroundJob) -> Any:
        self._jobs[job.job_id] = job
        self._execute_sync(job)
        if job.status == "FAILED":
            if job._last_exception:
                raise job._last_exception
            raise RuntimeError(job.error or "Background job execution failed")
        return job.result

    def get_job(self, job_id: str) -> Optional[BackgroundJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        jobs = list(self._jobs.values())
        if status:
            jobs = [j for j in jobs if j.status == status]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.to_dict() for j in jobs[:limit]]

    def _execute_sync(self, job: BackgroundJob) -> None:
        """Synchronous runner for testing environments."""
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        job.status = "RUNNING"
        while job.attempt < job.max_retries:
            job.attempt += 1
            try:
                res = job.func(*job.args, **job.kwargs)
                job.result = res
                job.status = "SUCCESS"
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                return
            except Exception as exc:
                job._last_exception = exc
                job.error = str(exc)
                err_code = getattr(exc, "error_code", getattr(exc, "code", ""))
                if isinstance(exc, (ValueError, TypeError)) or err_code in NON_RETRYABLE_ERRORS or job.attempt >= job.max_retries:
                    job.status = "FAILED"
                    job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                    logger.error(f"Job {job.job_id} ({job.job_type}) failed permanently: {exc}")
                    return
                job.status = "RETRYING"

    async def _run_job(self, job: BackgroundJob) -> None:
        """Asynchronous execution with exponential backoff."""
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        job.status = "RUNNING"

        while job.attempt < job.max_retries:
            job.attempt += 1
            try:
                if asyncio.iscoroutinefunction(job.func):
                    res = await job.func(*job.args, **job.kwargs)
                else:
                    res = await asyncio.to_thread(job.func, *job.args, **job.kwargs)
                job.result = res
                job.status = "SUCCESS"
                job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                logger.info(f"Job {job.job_id} ({job.job_type}) completed successfully.")
                return
            except Exception as exc:
                job.error = str(exc)
                err_code = getattr(exc, "error_code", "")
                if err_code in NON_RETRYABLE_ERRORS or job.attempt >= job.max_retries:
                    job.status = "FAILED"
                    job.completed_at = datetime.datetime.now(datetime.timezone.utc)
                    logger.error(f"Job {job.job_id} ({job.job_type}) failed on attempt {job.attempt}: {exc}")
                    return

                job.status = "RETRYING"
                backoff_sec = (2 ** (job.attempt - 1)) * 0.5  # 0.5s, 1.0s, 2.0s
                logger.warning(f"Job {job.job_id} failed attempt {job.attempt}. Retrying in {backoff_sec:.1f}s: {exc}")
                await asyncio.sleep(backoff_sec)


job_manager = JobManager()
