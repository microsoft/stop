import random
import numpy as np
from helpers import temp_override, read_file_as_str
from pebble import ThreadPool
from config import config

def utility(algorithm_str: str, mode: str = "val"):
    """
    Implements the Max-Cut utility function. Returns the average cut weight.
    If the algorithm requires more than 100 milliseconds to run per test, it is a failure.
    """
    # Uncomment to limit the number of times the algorithm can be used
    # uses = getattr(utility, "uses", 0)
    # if uses >= utility.budget:
    #     return 0
    # if not algorithm_str:
    #     print(f"algorithm_str is {repr(algorithm_str)}, returning 0")
    #     return 0
    # utility.uses = uses + 1

    n_tests = 100
    min_n_nodes = 50
    max_n_nodes = 200
    average_cut_weight = 0
    base_seed = 4321 if mode == "val" else 5678
    pool = ThreadPool()
    eps = 1e-2

    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except Exception as e:
        return eps

    for test_idx in range(n_tests):
        random.seed(base_seed + test_idx)  # Consistent seeding for evaluation
        np.random.seed(base_seed + test_idx)

        n_nodes = random.randint(min_n_nodes, max_n_nodes)
        p_edge = 0.4
        max_weight = 10

        # Generate random adjacency matrix
        adjacency_matrix = np.zeros((n_nodes, n_nodes))
        for i in range(n_nodes):
            for j in range(i+1, n_nodes):
                if random.random() < p_edge:
                    weight = random.randint(1, max_weight)
                    adjacency_matrix[i, j] = weight
                    adjacency_matrix[j, i] = weight

        # Run the algorithm to find the partition
        try:
            partition_future = pool.schedule(algorithm, (adjacency_matrix,))
            partition = partition_future.result(timeout=0.1)
            if len(partition) != n_nodes:
                return 0
            cut_weight = 0
            for i in range(n_nodes):
                for j in range(i+1, n_nodes):
                    if partition[i] != partition[j]:
                        cut_weight += adjacency_matrix[i, j]
        except Exception as e:
            if e.__class__.__name__ != "TimeoutError":
                print("Exception:", e)
            return eps

        average_cut_weight += cut_weight / n_tests / max_weight

    return max(average_cut_weight, eps)

utility.budget = config["utility_budget"]
fake_self_str = read_file_as_str(f"tasks/maxcut/utility.py")
utility.str = fake_self_str
utility.uses = 0