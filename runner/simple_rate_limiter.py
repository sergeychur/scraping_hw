import time
import threading


class SimpleRateLimiter:
    def __init__(self, rate):
        self._lock = threading.Lock()
        self._delta = 1. / rate
        self._last_called_ts = 0

    def get_delay(self, timestamp=None):
        with self._lock:
            expected_next_call_ts = self._last_called_ts + self._delta
            if timestamp is None:
                timestamp = time.time()
            self._last_called_ts = timestamp
            return max(expected_next_call_ts - timestamp, 0)

