from __future__ import annotations


class FakeClock:
    def __init__(self, initial: float = 0.0) -> None:
        self.current = initial
        self.sleeps: list[float] = []

    def now(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds

    def advance(self, seconds: float) -> None:
        self.current += seconds

