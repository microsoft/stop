import numpy as np
import random
from pebble import ThreadPool
from helpers import temp_override
import time

def generate_3sat_formula(n, m):
    """Generate a random 3-SAT formula with n variables and m clauses."""
    formula = []
    valid_assignment = [False] + [random.random() < 0.5 for _ in range(n)]
    while len(formula) < m:
        clause = random.sample(range(1, n + 1), 3)
        clause = [var if random.random() < 0.5 else -var for var in clause]
        # Check if the clause is satisfied by the valid assignment
        if any((valid_assignment[abs(lit)] > 0) == (lit > 0) for lit in clause):
            formula.append(clause)
    return formula

def check_3sat_formula(formula, assignment):
    return all(any((assignment[abs(lit)] > 0) == (lit > 0) for lit in clause) for clause in formula)

def utility(algorithm_str: str):
    """
    Implements the Random 3-SAT problem with n variables and m clauses.
    Returns the fraction of formulas solved successfully within the time limit.
    The algorithm must be extremely fast. If it takes more than 10 milliseconds to run, it is a failure.
    Your algorithm function must be named 'algorithm' and take a single argument, formula
    which is a list of m clauses, each containing exactly 3 literals.
    """
    n_tests = 100
    n = 50  # Number of variables
    m = int(4 * n)  # Number of clauses
    solved_count = 0
    pool = ThreadPool()

    try:
        exec(algorithm_str, globals())
    except:
        return 0

    for test_idx in range(n_tests):
        formula = generate_3sat_formula(n, m)
        try:
            assignment_future = pool.schedule(algorithm, (formula,))
            assignment = assignment_future.result(timeout=0.01)
            if check_3sat_formula(formula, assignment):
                solved_count += 1
        except Exception as e:
            return 0

    return solved_count / n_tests