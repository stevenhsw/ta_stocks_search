from threading import Lock

mylock = Lock()

def print_l(*a, **b):
    with mylock:
        print(*a, **b)
