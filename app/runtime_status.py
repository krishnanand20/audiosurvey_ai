import threading
import time
from typing import Optional


STATUS_LOCK = threading.RLock()

_scheduler_started_at: Optional[float] = None
_scheduler_heartbeat_at: Optional[float] = None
_worker_started_at: Optional[float] = None
_worker_heartbeat_at: Optional[float] = None

SCHEDULER_TIMEOUT_SEC = 45
WORKER_TIMEOUT_SEC = 20


def _now() -> float:
    return time.time()


def mark_scheduler_started() -> None:
    now = _now()
    with STATUS_LOCK:
        global _scheduler_started_at, _scheduler_heartbeat_at
        _scheduler_started_at = _scheduler_started_at or now
        _scheduler_heartbeat_at = now


def mark_scheduler_heartbeat() -> None:
    with STATUS_LOCK:
        global _scheduler_heartbeat_at
        _scheduler_heartbeat_at = _now()


def mark_worker_started() -> None:
    now = _now()
    with STATUS_LOCK:
        global _worker_started_at, _worker_heartbeat_at
        _worker_started_at = _worker_started_at or now
        _worker_heartbeat_at = now


def mark_worker_heartbeat() -> None:
    with STATUS_LOCK:
        global _worker_heartbeat_at
        _worker_heartbeat_at = _now()


def _service_snapshot(
    started_at: Optional[float],
    heartbeat_at: Optional[float],
    timeout_sec: int,
    paused: bool = False,
) -> dict:
    now = _now()
    age_sec = None if heartbeat_at is None else max(0, int(now - heartbeat_at))

    if not started_at:
        return {"status": "not_started", "label": "Not started", "age_sec": age_sec}

    if heartbeat_at is None:
        return {"status": "starting", "label": "Starting", "age_sec": age_sec}

    if (now - heartbeat_at) > timeout_sec:
        return {"status": "down", "label": "Down", "age_sec": age_sec}

    if paused:
        return {"status": "paused", "label": "Paused", "age_sec": age_sec}

    return {"status": "running", "label": "Running", "age_sec": age_sec}


def get_runtime_snapshot(paused: bool = False) -> dict:
    with STATUS_LOCK:
        scheduler = _service_snapshot(
            started_at=_scheduler_started_at,
            heartbeat_at=_scheduler_heartbeat_at,
            timeout_sec=SCHEDULER_TIMEOUT_SEC,
            paused=paused,
        )
        worker = _service_snapshot(
            started_at=_worker_started_at,
            heartbeat_at=_worker_heartbeat_at,
            timeout_sec=WORKER_TIMEOUT_SEC,
            paused=False,
        )

    return {
        "scheduler": scheduler,
        "worker": worker,
    }
