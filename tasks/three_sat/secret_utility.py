from pebble import ThreadPool
from tqdm import tqdm
from helpers import temp_override
import numpy as np
import random
import time
from helpers import read_file_as_str

def generate_3sat_formula(n, m):
    """Generate a random 3-SAT formula with n variables and m clauses."""
    formula = []
    valid_assignment = [False] + [random.random() < 0.5 for _ in range(n)]
    for _ in range(m ** 2):
        clause = random.sample(range(1, n + 1), 3)
        clause = [var if random.random() < 0.5 else -var for var in clause]
        # Check if the clause is satisfied by the valid assignment
        if any((valid_assignment[abs(lit)] > 0) == (lit > 0) for lit in clause):
            formula.append(clause)
        if len(formula) == m:
            break
    random.shuffle(formula)
    return formula

def check_3sat_formula(formula, assignment):
    success = all(any((assignment[abs(lit)] > 0) == (lit > 0) for lit in clause) for clause in formula)
    return success

def utility(algorithm_str: str, mode: str = "val"):
    """
    Implements the Random 3-SAT problem with n variables and m clauses.
    Returns the fraction of formulas solved successfully within the time limit.
    The algorithm must be extremely fast. If it takes more than 10 milliseconds to run, it is a failure.
    Your algorithm function must be named 'algorithm' and take a single argument, formula,
    which is a list of m clauses, each containing exactly 3 literals.
    """
    # Uncomment to limit the number of times the algorithm can be used
    # uses = getattr(utility, "uses", 0)
    # if uses >= utility.budget:
    #     return 0
    # if not algorithm_str:
    #     print(f"algorithm_str is {repr(algorithm_str)}, returning 0")
    #     return 0
    # utility.uses = uses + 1

    n_tests = 30
    min_n = 5  # Min number of variables
    max_n = 50  # Max number of variables
    solved_count = 0
    base_seed = 4321 if mode == "val" else 5678
    timeout = 0.1
    eps = 1e-2
    join_pool = False
    
    pool = ThreadPool()

    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except:
        pool.stop()
        if join_pool:
            pool.join()
        return eps

    for test_idx in tqdm(range(n_tests)):
        random.seed(base_seed + test_idx)  # Consistent seeding for evaluation
        n = random.randint(min_n, max_n)
        m = int(4 * n)  # Number of clauses (change 4 to a different number to adjust difficulty)
        formula = generate_3sat_formula(n, m)
        try:
            formula_copy = formula.copy()
            time_start = time.time()
            if isinstance(pool, ThreadPool):
                assignment_future = pool.schedule(algorithm, (formula_copy,))
            else:
                assignment_future = pool.schedule(algorithm, (formula_copy,), timeout=timeout)
            assignment = assignment_future.result(timeout=timeout)
            time_end = time.time()
            if time_end - time_start > timeout:
                solved_count += eps
                continue
            # Validate the solution
            if check_3sat_formula(formula, assignment):
                solved_count += 1
            else:
                solved_count += eps
        except Exception as e:
            if not isinstance(e, TimeoutError):
                pool.stop()
                return eps

    pool.stop()
    if join_pool:
        pool.join()
    print(f"average_correct: {solved_count / n_tests}")
    return max(solved_count / n_tests, eps)

from config import config
from helpers import read_file_as_str
import os
utility.budget = config["utility_budget"]
# get the name of the file's directory
fake_self_str = read_file_as_str(f"tasks/three_sat/utility.py")
utility.str = fake_self_str
utility.uses = 0