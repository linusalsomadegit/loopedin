

class _Scheduler:
    def __init__(self):
        self.running = False

    def start(self):
        if not self.running:
            self.running = True

    def stop(self):
        if self.running:
            self.running = False


# Create a single instance
Scheduler = _Scheduler()
