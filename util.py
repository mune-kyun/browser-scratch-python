import time
from time import perf_counter

def elapsed_ms(func, *args, **kwargs):
    start_time = perf_counter()
    res = func(*args, **kwargs)
    end_time = perf_counter()

    elapsed_time = (end_time - start_time) * 1000
    return elapsed_time, res