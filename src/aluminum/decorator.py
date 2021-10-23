import functools
from typing import Callable
from aluminum import seesion_lock
from aluminum.exceptions import SeesionLockError

test = True

def check_lock(func: Callable):
    
    def wrapper(*args, **kwargs):
        if seesion_lock:
            raise SeesionLockError
        seesion_lock = True
        return func(*args, **kwargs)
    return wrapper

@check_lock
def test():
    print('awa')

if __name__ == '__main__':
    test()
