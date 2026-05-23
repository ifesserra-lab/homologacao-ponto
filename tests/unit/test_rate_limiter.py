from homologacao_ponto.infrastructure import RateLimiter
from fixtures.clock import FakeClock


def test_rate_limiter_waits_until_min_interval() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock=clock.now, sleeper=clock.sleep)

    assert limiter.wait_before_action() == 0
    clock.advance(0.5)

    waited = limiter.wait_before_action()

    assert waited == 1.5
    assert clock.sleeps == [1.5]
