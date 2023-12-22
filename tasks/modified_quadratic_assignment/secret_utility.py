import numpy as np
from pebble import ThreadPool
from helpers import temp_override
import time

def utility(algorithm_str: str, mode: str = "val"):
    """
    Implements the Modified Quadratic Assignment Problem (MQAP) with n facilities/locations.
    Returns the objective value, where higher is better.
    The algorithm must be extremely fast. If it takes more than 500 milliseconds to run, it is a failure.
    Your algorithm function must be named 'algorithm' and take three arguments: F, D, and P, 
    which are numpy arrays of shape (n, n) containing the flow, distance, and preference matrices.
    """
    # Uncomment to limit the number of times the algorithm can be used
    # uses = getattr(utility, "uses", 0)
    # if uses >= utility.budget:
    #     return 0
    # if not algorithm_str:
    #     print(f"algorithm_str is {repr(algorithm_str)}, returning 0")
    #     return 0
    # utility.uses = uses + 1

    n_tests = 10
    n = 15  # Number of facilities and locations
    lambda_value = 0.5  # Preference weight
    average_objective = 0
    base_seed = 4321 if mode == "val" else 5678
    pool = ThreadPool()
    eps = 1e-2
    scale = n * n

    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except:
        return eps

    for test_idx in range(n_tests):
        np.random.seed(base_seed + test_idx)  # Consistent seeding for evaluation
        F = np.random.rand(n, n)
        D = np.random.rand(n, n)
        P = np.random.rand(n, n)
        
        try:
            start_time = time.time()
            assignment_future = pool.schedule(algorithm, (F, D, P))
            assignment = assignment_future.result(timeout=0.5)
            total_time = time.time() - start_time

            if set(assignment) == set(range(n)):
                objective = sum(F[i, j] * D[assignment[i], assignment[j]] for i in range(n) for j in range(n))
                objective -= lambda_value * sum(P[i, assignment[i]] for i in range(n))
                objective += total_time
            else:
                objective = 0.0

            average_objective += objective / n_tests
        except Exception as e:
            average_objective += 0.0

    return max(average_objective / scale, eps)

from config import config
from helpers import read_file_as_str
import os
utility.budget = config["utility_budget"]
fake_self_str = read_file_as_str(f"tasks/modified_quadratic_assignment/utility.py")
utility.str = fake_self_str
utility.uses = 0