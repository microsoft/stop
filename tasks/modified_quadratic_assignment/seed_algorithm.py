import numpy as np
from random import randint, random
from copy import deepcopy

def algorithm(F, D, P):
    def mqap_objective(assignment):
        objective = sum(F[i, j] * D[assignment[i], assignment[j]] for i in range(n) for j in range(n))
        objective -= lambda_value * sum(P[i, assignment[i]] for i in range(n))
        return objective

    def swap_random(assignment):
        i, j = randint(0, n - 1), randint(0, n - 1)
        while i == j:
            j = randint(0, n - 1)
        assignment[i], assignment[j] = assignment[j], assignment[i]

    n = len(F)
    lambda_value = 0.5
    max_iterations = 1000
    temperature = 1.0
    cooling_rate = 0.99

    assignment = list(range(n))
    best_assignment = deepcopy(assignment)
    best_objective = mqap_objective(assignment)

    for _ in range(max_iterations):
        temperature *= cooling_rate
        if temperature == 0:
            break

        new_assignment = deepcopy(assignment)
        swap_random(new_assignment)
        new_objective = mqap_objective(new_assignment)
        delta_objective = new_objective - mqap_objective(assignment)

        if delta_objective < 0 or random() < np.exp(-delta_objective / temperature):
            assignment = new_assignment

            if new_objective < best_objective:
                best_assignment = deepcopy(assignment)
                best_objective = new_objective

    return best_assignment