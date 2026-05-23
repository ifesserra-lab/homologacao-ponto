from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


Clock = Callable[[], float]
Sleeper = Callable[[float], None]


@dataclass
class RateLimiter:
    min_interval_seconds: float = 2.0
    clock: Clock = time.monotonic
    sleeper: Sleeper = time.sleep
    _last_action_at: float | None = None

    def wait_before_action(self) -> float:
        now = self.clock()
        if self._last_action_at is None:
            self._last_action_at = now
            return 0.0
        elapsed = now - self._last_action_at
        wait_for = max(0.0, self.min_interval_seconds - elapsed)
        if wait_for:
            self.sleeper(wait_for)
            now = self.clock()
        self._last_action_at = now
        return wait_for

