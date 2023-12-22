import random
import numpy as np

def utility(algorithm_str: str):
    """
    Implements the parity learning task. Returns the number of correct predictions.
    """

    n_tests = 3
    average_correct = 0

    try:
        exec(algorithm_str, globals())
    except:
        return 0

    for _ in range(n_tests):
        n_bits = 10
        p_true = 0.3
        n_train_samples = 80
        n_test_samples = 20
        true_bits = np.random.binomial(1, p_true, n_bits)
        
        samples = np.random.binomial(1, 0.5, (n_train_samples + n_test_samples, n_bits))
        masked_samples = samples * true_bits
        parity = np.sum(masked_samples, axis=1) % 2
        train_samples = samples[:n_train_samples]
        train_parity = parity[:n_train_samples]

        test_samples = samples[n_train_samples:]
        test_parity = parity[n_train_samples:]

        # Because algorithm is a string, we can't call it directly. Instead, we can use eval to evaluate it as a Python expression.
        try:
            predictions = algorithm(train_samples, train_parity, test_samples)
            correct = np.sum(predictions == test_parity) / n_test_samples
        except:
            correct = 0
        average_correct += correct / n_tests

    return average_correct