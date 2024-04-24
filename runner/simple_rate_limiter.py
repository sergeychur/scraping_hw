import threading
import time


class SimpleRateLimiter:
    def __init__(self, rate):
        self._lock = threading.Lock()
        self._delta = 1. / rate
        self._last_called_ts = time.time()

    def get_delay(self, now=None):
        with self._lock:
            if now is None:
                now = time.time()
            expected_next_call_ts = self._last_called_ts + self._delta
            delay = max(expected_next_call_ts - now, 0)
            self._last_called_ts = max(expected_next_call_ts, now)
            return delay
