from time import time,sleep

class Limiter:
    rpm = None
    last_polled = None
    def __init__(self,rate_limit,type="rpm"):
        match type:
            case "rpm":
                self.rpm = rate_limit
            case "rph":
                self.rpm = rate_limit/60
            case _:
                self.rpm = rate_limit
        self.last_polled = time()

    def wait(self):
        max_wait = 60 / self.rpm
        buffer = min(max_wait*2,0.5)
        elapsed = time() - self.last_polled
        wait_seconds = max_wait - elapsed
        if wait_seconds > -buffer:
            #print("waiting for", wait_seconds, "seconds")
            sleep(max(wait_seconds,0) + buffer)
        self.last_polled = time()