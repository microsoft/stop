from pebble import ThreadPool
import numpy as np
import os
import time
import traceback
from language_model import LanguageModel
from tqdm import tqdm

from config import config
from helpers import (
    read_file_as_str, generate_seed_algorithm, write_str_to_file,
    temp_override, end_pool_if_used, write_log
)

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

# print the current directory
base_secret_utility_str = read_file_as_str(f"tasks/{config['subtask']}/secret_utility.py")
base_utility_str = read_file_as_str(f"tasks/{config['subtask']}/utility.py")
try:
    base_algorithm_str = read_file_as_str(f"tasks/{config['subtask']}/seed_algorithm.py")
except:
    base_algorithm_str = generate_seed_algorithm(base_utility_str)
    write_str_to_file(base_algorithm_str, f"tasks/{config['subtask']}/seed_algorithm.py")

def get_improver(improve_str: str, utility, mode: str = "val", language_model=None):
    """
    Uses the improvement algorithm in improve_str to improve the algorithm in algorithm_str, according to the utility function.
    """
    try:
        new_improve_algorithm = temp_override(improve_str, "improve_algorithm")
        improved_algorithm_str = new_improve_algorithm(base_algorithm_str, utility, language_model)
        return improved_algorithm_str
    except Exception as e:
        print("Definition failed with exception:", e)
        print(traceback.format_exc())
        raise e

def pre_utility_hook(cur_utility_fn):
    cur_utility_fn.uses = 0
    language_model = LanguageModel(budget=config['language_model_call_budget'])
    return language_model

def create_handled_fn(fn, handle_exceptions, log_usage, pool, timeout=None, fail_value=""):
    def handled_fn(*args, **kwargs):
        try:
            if timeout is not None:
                fn_future = pool.schedule(fn, args=args, kwargs=kwargs)
                return fn_future.result(timeout=timeout)
            return fn(*args, **kwargs)
        except Exception as e:
            print("Exception in eval:", e)
            print(traceback.format_exc())
            if not handle_exceptions:
                end_pool_if_used(pool, join_pools=config["join_pools"])
                raise e
            if not log_usage:
                end_pool_if_used(pool, join_pools=config["join_pools"])
                return e
            return fail_value
    return handled_fn

def meta_utility(improve_str: str, mode: str = "val", log_usage: bool = False, handle_exceptions: bool = True):
    """
    Uses the improvement algorithm in improve_str to improve the algorithm in algorithm_str, according to the utility function.
    """
    meta_utility.uses = getattr(meta_utility, "uses", 0) + 1
    if meta_utility.uses > meta_utility.budget:
        print("Ran out of uses for meta-utility.")
        return 0
    if not improve_str:
        print(f"improve_str is {repr(improve_str)}, returning 0")
        return 0
    n_tests = config['meta_utility_tests']
    use_timeout = False
    use_parallel = False
    # We can't use parallelism if we're not using timeout
    assert not (use_parallel and not use_timeout)
    expected_utility_val = 0
    expected_utility_test = 0
    eval_idx = str(int(time.time()))
    run_id = max([results_folder for results_folder in os.listdir("results")], key=lambda x: int(x.split("_")[0]))
    utility = temp_override(base_secret_utility_str, "utility")

    pool = ThreadPool() if use_timeout else None
    improved_algorithm_futures = []
    improved_algorithm_strs = []
    if use_parallel:
        for test_idx in tqdm(range(n_tests)):
            language_model = pre_utility_hook(utility)
            improved_algorithm_future = pool.schedule(get_improver, (improve_str, utility, mode, language_model))
            improved_algorithm_futures.append(improved_algorithm_future)
        for improved_algorithm_future in improved_algorithm_futures:
            utility.uses = 0  # In case utility points to the same object each time
            get_improver_wrapped = create_handled_fn(improved_algorithm_future.result, handle_exceptions, log_usage, pool)()
            improved_algorithm_str = get_improver_wrapped(timeout=60 * 60)
            if isinstance(improved_algorithm_str, Exception):
                return 0
            improved_algorithm_strs.append(improved_algorithm_str)
    else:
        for test_idx in tqdm(range(n_tests)):
            language_model = pre_utility_hook(utility)
            timeout = 60 * 60 if use_timeout else None
            get_improver_wrapped = create_handled_fn(get_improver, handle_exceptions, log_usage, pool, timeout=timeout)
            improved_algorithm_str = get_improver_wrapped(improve_str, utility, mode, language_model)
            if isinstance(improved_algorithm_str, Exception):
                return 0
            improved_algorithm_strs.append(improved_algorithm_str)
    end_pool_if_used(pool, join_pools=config["join_pools"])
    for test_idx, improved_algorithm_str in enumerate(improved_algorithm_strs):
        if not improved_algorithm_str:
            continue
        # Save the improved algorithm to a file
        # First, find the most recent folder in results
        # Then, save the algorithm to that folder
        time_elapsed = int(eval_idx) - int(run_id.split("_")[0])
        write_str_to_file(base_algorithm_str, f"results/{run_id}/base_algorithm_{time_elapsed}_{test_idx}.py")
        write_str_to_file(improved_algorithm_str, f"results/{run_id}/improved_algorithm_{time_elapsed}_{test_idx}.py")
        utility.uses = 0
        utility_wrapped = create_handled_fn(utility, handle_exceptions, log_usage, None, fail_value=0)
        new_utility_val = utility_wrapped(improved_algorithm_str, mode="val")
        if isinstance(new_utility_val, Exception):
            return 0
        # Also log test
        if log_usage:
            print("Evaluating improved algorithm on test")
            utility.uses = 0
            utility_wrapped = create_handled_fn(utility, handle_exceptions, log_usage, None, fail_value=0)
            new_utility_test = utility_wrapped(improved_algorithm_str, mode="test")
            if isinstance(new_utility_test, Exception):
                return 0
            expected_utility_test += new_utility_test / n_tests
        expected_utility_val += new_utility_val / n_tests
    if log_usage:
        write_log(expected_utility_val, expected_utility_test, run_id)
    return expected_utility_val

# We're in secret_utility.py - we want the string of utility.py
fake_self_str = read_file_as_str(f"tasks/{config['task']}/utility.py")
meta_utility.budget = config['meta_utility_budget']
meta_utility.str = fake_self_str