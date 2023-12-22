from pebble import ThreadPool
from helpers import temp_override, read_file_as_str
import multiprocess
import random
import numpy as np
import time
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

    if mode == "test":
        n_tests = 50
    else:
        n_tests = 20
    average_correct = 0
    eps = 1e-6
    base_seed = 4321 if mode == "val" else 5678
    pool = ThreadPool()

    try:
        algorithm = temp_override(algorithm_str, "algorithm")
    except Exception as e:
        print(e.__class__.__name__, "Exception in utility:", e)
        print("algorithm_str:", algorithm_str)
        pool.stop()
        if config['join_pools']:
            pool.join()
        return 0

    for test_idx in range(n_tests):
        np.random.seed(base_seed + test_idx)
        random.seed(base_seed + test_idx)

        n_bits = 10
        p_true = 0.3
        n_train_samples = 100
        n_test_samples = 20
        noise_level = 0.05
        true_bits = np.random.binomial(1, p_true, n_bits)
        
        samples = np.random.binomial(1, 0.5, (n_train_samples + n_test_samples, n_bits))
        masked_samples = samples * true_bits
        parity = np.sum(masked_samples, axis=1) % 2
        train_samples = samples[:n_train_samples]
        train_parity = parity[:n_train_samples]
        parity_noise = np.random.binomial(1, noise_level, n_train_samples)
        train_parity = (train_parity + parity_noise) % 2

        test_samples = samples[n_train_samples:]
        test_parity = parity[n_train_samples:]

        # Because algorithm is a string, we can't call it directly. Instead, we can use eval to evaluate it as a Python expression.
        try:
            timeout = 2
            start_time = time.time()
            predictions_future = pool.schedule(algorithm, (train_samples, train_parity, test_samples))
            predictions = predictions_future.result(timeout=timeout)
            end_time = time.time()
            if end_time - start_time > timeout:
                pool.stop()
                if config['join_pools']:
                    pool.join()
                print("Timeout in utility, returning 0")
                return eps
            # Make them both row vectors
            predictions = np.array(predictions).reshape(-1)
            test_parity = np.array(test_parity).reshape(-1)
            correct = np.sum(predictions == test_parity) / n_test_samples
        except Exception as e:
            print(e.__class__.__name__, "Exception in utility:", e)
            pool.stop()
            if config['join_pools']:
                pool.join()
            return eps
        average_correct += correct / n_tests
    print("average_correct:", average_correct)
    pool.stop()
    if config['join_pools']:
        pool.join()
    return average_correct

utility.budget = config["utility_budget"]
fake_self_str = read_file_as_str(f"tasks/parity_noise/utility.py")
utility.str = fake_self_str
utility.uses = 0