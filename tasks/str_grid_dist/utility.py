import random
import time

def utility(algorithm_str: str):
    """Implements the str_grid_dist task. Returns a value between 0 and 1."""

    try:
        exec(algorithm_str, globals())
    except:
        return 0.0

    scores = []    
    for _ in range(10):
        length = random.randint(1, 30)
        t = "".join(random.choice("AB") for _ in range(length))
        s = "".join(random.choice("AB") for _ in range(length))
        dist = grid_dist(s, t)
        scores.append(score_test(t, dist, algorithm))
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
            return 0.0
        if d == dist:
            return 1.0  # perfect!
        else:
            return 0.5 - abs(d - dist)/(6*len(t)) # between 0 and 0.5
    except:
        return 0.0  # error