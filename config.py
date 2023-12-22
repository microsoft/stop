n = 6
m = 4

config = {
    "use_seed_algorithm": True,
    "iterative": True,
    "task": "meta_optimization",
    "subtask": "parity_noise",
    "use_improver": True,
    "n_iterations": 6,
    'use_language_model_cache': False,
    'max_responses_per_call': n,
    'language_model_call_budget': m,
    'meta_utility_budget': n * m + 1,
    'utility_budget': n * m + 1,
    'meta_utility_tests': 5,
    'transfer_eval_type': 'improved',
    'use_timeout_in_improver': False,
    'join_pools': False,
}