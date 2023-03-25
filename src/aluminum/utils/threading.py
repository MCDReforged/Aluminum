import threading

from aluminum.utils.message_io import print_msg
from aluminum.utils.translation import trans


class TaskScheduler:
    """
    A class that encapsulates a scheduler and allows you to add one-time and interval tasks,
    cancel tasks, and stop the scheduler.
    """

    def __init__(self, interval: int, target: callable, thread_name="TaskScheduler", arguments: tuple = ()):
        """
        Initialize the scheduler with a specified thread name.
        """
        self.thread_name = thread_name
        self.target = target
        self.interval = interval
        self.arguments = arguments
        self.tasks = {}
        self.lock = threading.Lock()

    def start(self):
        self.target(*self.arguments)
        self.timer = threading.Timer(self.interval, self.start)
        self.timer.setName(self.thread_name)
        self.timer.start()

    def stop(self):
        self.timer.cancel()


def check_lock(func):
    """
    Decorator to wrap a function to ensure that the function is executed under the session lock.
    """
    def wrapper(s, source, *args, **kwargs):
        if s.lock.locked():
            print_msg(source, trans('§cSeesion in use.'))
            return None
        with s.lock:
            return func(s, source, *args, **kwargs)
    return wrapper
