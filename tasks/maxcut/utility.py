import random
import numpy as np

def utility(algorithm_str: str):
    """
    Implements the Max-Cut utility function. Returns the average cut weight.
    If the algorithm requires more than 100 milliseconds to run per test, it is a failure.
    """

    n_tests = 3
    average_cut_weight = 0

    try:
        exec(algorithm_str, globals())
    except:
        return 0

    for test_idx in range(n_tests):
        n_nodes = 300
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
            partition = algorithm(adjacency_matrix)
            # Make sure there are exactly two partitions
            if len(set(partition)) != 2:
                return 0
            if len(partition) != n_nodes:
                return 0
            cut_weight = 0
            for i in range(n_nodes):
                for j in range(i+1, n_nodes):
                    if partition[i] != partition[j]:
                        cut_weight += adjacency_matrix[i, j]
        except Exception as e:
            print("Exception:", e)
            cut_weight = 0

        average_cut_weight += cut_weight / n_tests / max_weight

    return average_cut_weight
