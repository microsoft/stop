import random
import numpy as np
from helpers import temp_override, read_file_as_str
from config import config

def utility(algorithm_str: str, mode: str = "val"):
    """
    Implements the parity learning task. Returns the number of correct predictions.
    """

    uses = getattr(utility, "uses", 0)
    if uses >= utility.budget:
        return 0
    if not algorithm_str:
        print(f"algorithm_str is {repr(algorithm_str)}, returning 0")
        return 0
    utility.uses = uses + 1

    n_tests = 20
    average_correct = 0
    base_seed = 4321 if mode == "val" else 5678

    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except Exception as e:
        return 0

    for test_idx in range(n_tests):
        np.random.seed(base_seed + test_idx)
        random.seed(base_seed + test_idx)

        n_bits = 10
        p_true = 0.3
        n_train_samples = 100
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
        except Exception as e:
            print("Exception:", e)
            correct = 0
        average_correct += correct / n_tests
    return average_correct

utility.budget = config["utility_budget"]
# get the name of the file's directory
fake_self_str = read_file_as_str(f"tasks/parity_noiseless/utility.py")
utility.str = fake_self_str
utility.uses = 0