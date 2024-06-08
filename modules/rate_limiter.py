import time

class RateLimiter:
    def __init__(self, rate_limit_per_sec):
        self.rate_limit_per_sec = rate_limit_per_sec
        self.last_request_time = 0

    def ready(self):
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time
        if elapsed_time < 1 / self.rate_limit_per_sec:
            time.sleep((1 / self.rate_limit_per_sec) - elapsed_time)
        self.last_request_time = time.time()
        return True