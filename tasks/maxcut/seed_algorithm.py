def algorithm(adjacency_matrix):
    n_nodes = len(adjacency_matrix)
    partition = [-1] * n_nodes
    unpartitioned_nodes = set(range(n_nodes))

    while len(unpartitioned_nodes) > 0:
        max_cut_weight = -1
        max_cut_node = None
        max_cut_partition = None

        for node in unpartitioned_nodes:
            for partition_id in [0, 1]:
                cut_weight = 0
                for neighbor, weight in enumerate(adjacency_matrix[node]):
                    if partition[neighbor] == 1 - partition_id:
                        cut_weight += weight

                if cut_weight > max_cut_weight:
                    max_cut_weight = cut_weight
                    max_cut_node = node
                    max_cut_partition = partition_id

        partition[max_cut_node] = max_cut_partition
        unpartitioned_nodes.remove(max_cut_node)

    return partition