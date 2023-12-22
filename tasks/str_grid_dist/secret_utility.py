import random
import time
import numpy as np
from pebble import ThreadPool
from helpers import temp_override, read_file_as_str
from config import config

def utility(algorithm_str: str, mode: str = "val"):
    """
    Implements the str_grid_dist task. Returns a value between -1 and 1.
    """
    # Uncomment to limit the number of times the algorithm can be called
    # uses = getattr(utility, "uses", 0)
    # if uses >= utility.budget:
    #     return 0
    # if not algorithm_str:
    #     print(f"algorithm_str is {repr(algorithm_str)}, returning 0")
    #     return 0
    # utility.uses = uses + 1

    base_seed = 4321 if mode == "val" else 5678
    pool = ThreadPool()
    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except:
        pool.stop()
        if config['join_pools']:
            pool.join()
        return 0.0

    scores = []    
    for test_idx in range(50):
        np.random.seed(base_seed + test_idx)
        random.seed(base_seed + test_idx)
        length = random.randint(1, 30)
        t = "".join(random.choice("AB") for _ in range(length))
        s = "".join(random.choice("AB") for _ in range(length))
        dist = grid_dist(s, t)

        # Because algorithm is a string, we can't call it directly. Instead, we can use eval to evaluate it as a Python expression.
        try:
            timeout = 1
            predictions_future = pool.schedule(score_test, (t, dist, algorithm))
            predictions = predictions_future.result(timeout=timeout)
            scores.append(predictions)
        except Exception as e:
            print("Exception in utility:", e)
            print(e.__class__.__name__)
            scores.append(0.0)
    pool.stop()
    if config['join_pools']:
        pool.join()
    return sum(scores) / len(scores)
        
def grid_dist(s: str, t: str):
    assert isinstance(s, str) and isinstance(t, str) and len(s) == len(t) and set(s + t) <= set("AB")
    ans = sum(a != b for a, b in zip(s, t))
    ans += sum(a != b for a, b in zip(s, s[1:]))
    ans += sum(a != b for a, b in zip(t, t[1:]))
    return ans


def score_test(t: str, dist: int, find_at_dist: callable, max_time=0.1) -> float:
    start_time = time.time()        
    try:
        s = find_at_dist(t, dist)
        d = grid_dist(s, t)
        if time.time() - start_time > max_time:
            return 0
        if d == dist:
            return 1.0  # perfect!
        else:
            return 0.5 - abs(d - dist)/(6*len(t)) # between 0 and 0.5
    except:
        return 0  # error

utility.budget = config["utility_budget"]
# get the name of the file's directory
fake_self_str = read_file_as_str(f"tasks/str_grid_dist/utility.py")
utility.str = fake_self_str
utility.uses = 0