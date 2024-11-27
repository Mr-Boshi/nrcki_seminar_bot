from time import time


class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.last_request_time = self.int_time()

    def ready(self):
        if self.remain() <= 0:
            self.flush()
            return True
        else:
            return False

    def int_time(self):
        return int(round(time()))

    def flush(self):
        self.last_request_time = self.int_time()

    def remain(self):
        return self.rate_limit - (self.int_time() - self.last_request_time)
