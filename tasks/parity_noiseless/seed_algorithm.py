import numpy as np

def algorithm(train_samples, train_parity, test_samples):
    predictions = np.random.binomial(1, 0.5, len(test_samples))
    return predictions