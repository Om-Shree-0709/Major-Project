import time
from collections import defaultdict


class RateLimiter:

    def __init__(self, max_requests=60, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def allow_request(self, client_id):

        now = time.time()
        window_start = now - self.window

        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > window_start
        ]

        if len(self.requests[client_id]) >= self.max_requests:
            return False

        self.requests[client_id].append(now)
        return True