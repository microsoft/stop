import numpy as np
from pebble import ThreadPool
from helpers import temp_override
import time

def utility(algorithm_str: str):
    """
    Implements the Modified Quadratic Assignment Problem (MQAP) with n facilities/locations.
    Returns the objective value, where higher is better.
    The algorithm must be extremely fast. If it takes more than 500 milliseconds to run, it is a failure.
    Your algorithm function must be named 'algorithm' and take three arguments: F, D, and P, 
    which are numpy arrays of shape (n, n) containing the flow, distance, and preference matrices.
    """
    n_tests = 20
    n = 15  # Number of facilities and locations
    lambda_value = 0.5  # Preference weight
    average_objective = 0
    pool = ThreadPool()

    try:
        exec(algorithm_str, globals())
    except:
        return 0

    for test_idx in range(n_tests):
        F = np.random.rand(n, n)
        D = np.random.rand(n, n)
        P = np.random.rand(n, n)
        
        try:
            start_time = time.time()
            assignment_future = pool.schedule(algorithm, (F, D, P))
            assignment = assignment_future.result(timeout=0.01)
            total_time = time.time() - start_time

            if set(assignment) == set(range(n)):
                objective = sum(F[i, j] * D[assignment[i], assignment[j]] for i in range(n) for j in range(n))
                objective -= lambda_value * sum(P[i, assignment[i]] for i in range(n))
                objective += total_time
            else:
                objective = 0

            average_objective += objective / n_tests
        except Exception as e:
            average_objective += 0

    return average_objective
