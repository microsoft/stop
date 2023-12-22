from tasks.meta_optimization.secret_seed_algorithm import improve_algorithm as initial_improve_algorithm
from helpers import (
    load_seed_algorithm, write_str_to_file,
    generate_run_id, get_utility_strs,
    temp_override, read_file_as_str, end_pool_if_used
)
from config import config
from pebble import ProcessPool as Pool
import multiprocess
from language_model import cache_counter, LanguageModel
import time
import os
import traceback
import argparse

use_seed_algorithm = config["use_seed_algorithm"]
task = config["task"]

utility_str, secret_utility_str = get_utility_strs(task)
from tasks.meta_optimization.secret_utility import meta_utility
# Wipe usage_log.jsonl
with open("usage_log.jsonl", "w") as f:
    f.write("")

def pre_utility_hook(cur_utility_fn):
    """
    A hook function that resets the usage count of the current utility function,
    initializes a new language model, and clears the cache counter.

    Args:
        cur_utility_fn: The current utility function.

    Returns:
        A new language model.
    """
    cur_utility_fn.uses = 0
    language_model = LanguageModel(budget=config['language_model_call_budget'])
    cache_counter.clear()
    return language_model

def try_load_seed_algorithm(improver_filename, cur_utility_fn):
    """
    Attempts to load the seed algorithm from a file.

    Args:
        improver_filename: The name of the file containing the seed algorithm.
        cur_utility_fn: The current utility function.

    Returns:
        The loaded seed algorithm if successful, None otherwise.
    """
    try:
        improver_str = read_file_as_str(f"results/{resume_from}/{improver_filename}")
        base_meta_algorithm_str = improver_str
        improve_algorithm = temp_override(improver_str, "improve_algorithm")
        cur_utility_fn(base_meta_algorithm_str, handle_exceptions=False)  # Make sure it runs
        return improver_str, base_meta_algorithm_str, improve_algorithm
    except Exception as e:
        print("Failed to load from", improver_filename, "with exception", e)
        print(traceback.format_exc())
        return None, None, None

def get_from_seed(seed_filenames, evaluated_initial_utility, cur_utility_fn):
    """
    Attempts to load the seed algorithm from a list of filenames.

    Args:
        seed_filenames: The list of filenames containing the seed algorithms.
        evaluated_initial_utility: A boolean indicating whether the initial utility has been evaluated.
        cur_utility_fn: The current utility function.

    Returns:
        A tuple containing the loaded seed algorithm, the base meta algorithm, the improve algorithm, 
        and a boolean indicating whether the initial utility has been evaluated.
    """
    loaded_successfully = False
    while len(seed_filenames) > 0:
        improver_filename = seed_filenames.pop()
        improver_str, base_meta_algorithm_str, improve_algorithm = try_load_seed_algorithm(improver_filename, cur_utility_fn)
        if improver_str is not None:
            loaded_successfully = True
            break
    if not loaded_successfully:
        improver_str = load_seed_algorithm("meta_optimization", utility_str, use_seed_algorithm)
        base_meta_algorithm_str = load_seed_algorithm(task, utility_str, use_seed_algorithm)
        improve_algorithm = initial_improve_algorithm
        cur_utility_fn(base_meta_algorithm_str, log_usage=not evaluated_initial_utility)
        evaluated_initial_utility = True
    return improver_str, base_meta_algorithm_str, improve_algorithm, evaluated_initial_utility

def initialize_pool(use_timeout):
    """
    Initializes the process pool, if necessary.
    """
    if not use_timeout:
        return None
    return Pool(context=multiprocess.get_context('fork'))

def initialize_seed_list(resume_from):
    """
    Initializes the list of seed algorithm filenames that can be used for the optimization.

    Args:
        resume_from: The name of the run to resume from.

    Returns:
        A tuple containing the list of seed algorithms and the starting iteration number.
    """
    if resume_from is None:
        return [], 0
    
    seed_algorithms = [
        f for f in os.listdir(f"results/{resume_from}")
        if f.startswith("improved_algorithm") and f.count("_") == 2
    ]
    seed_algorithm_indices = [int(f.split("_")[-1].split(".")[0]) for f in seed_algorithms]
    start_iter = max(seed_algorithm_indices) + 1
    seed_zip = list(sorted(zip(seed_algorithm_indices, seed_algorithms)))
    seed_list = [f for _, f in seed_zip]
    return seed_list, start_iter

def attempt_algorithm_improvement(algorithm_to_improve, cur_utility_fn, improve_algorithm, previous_improve_algorithm):
    """
    Attempts to improve the given algorithm using the specified improve algorithm.

    Returns:
        A tuple containing a boolean indicating whether the improvement was successful, the new algorithm string, and the improve algorithm used.
    """
    pool = initialize_pool(config["use_timeout_in_improver"])
    language_model = pre_utility_hook(cur_utility_fn)
    successful_improvement = False
    new_algorithm_str = None
    
    try:
        if config["use_timeout_in_improver"]:
            new_algorithm_future = pool.schedule(improve_algorithm, (algorithm_to_improve, cur_utility_fn, language_model))
            new_algorithm_str = new_algorithm_future.result(timeout=2 * 60 * 60)
        else:
            new_algorithm_str = improve_algorithm(algorithm_to_improve, cur_utility_fn, language_model)
        language_model = pre_utility_hook(cur_utility_fn)
        checked_utility = cur_utility_fn(new_algorithm_str, log_usage=True)
        if checked_utility == 0:
            raise Exception("Checked utility is 0")
        successful_improvement = True  
    except Exception as e:
        print("Exception in improving, reverting to previous algorithm:", e, "\n", traceback.format_exc())
        improve_algorithm = previous_improve_algorithm

    end_pool_if_used(pool, join_pools=config["join_pools"])
    return successful_improvement, new_algorithm_str, improve_algorithm

def run_improver_main(resume_from=None):
    """
    The main function for the improver. Iteratively improves the target algorithm using the improve algorithm.
    If self target is enabled, the algorithm being improved is the same as the improve algorithm.
    """
    is_new_run = resume_from is None
    evaluated_initial_utility = not is_new_run
    cur_utility_fn = meta_utility
    seed_list, start_iter = initialize_seed_list(resume_from)
    improver_str, algorithm_to_improve, improve_algorithm, evaluated_initial_utility = get_from_seed(
        seed_list, evaluated_initial_utility, cur_utility_fn)
    _, _, previous_improve_algorithm, evaluated_initial_utility = get_from_seed(
        seed_list, evaluated_initial_utility, cur_utility_fn)

    for cur_iter in range(start_iter, config["n_iterations"]):
        write_str_to_file(algorithm_to_improve, f"results/{run_id}/seed_algorithm_{cur_iter}.py")
        successful_improvement, new_algorithm_str, improve_algorithm = attempt_algorithm_improvement(
            algorithm_to_improve, cur_utility_fn, improve_algorithm, previous_improve_algorithm
        )

        if successful_improvement:
            # Save algorithm to file
            write_str_to_file(new_algorithm_str, f"results/{run_id}/improved_algorithm_{cur_iter}.py")
            if config["iterative"]:
                improver_str = new_algorithm_str
            algorithm_to_improve = new_algorithm_str
            previous_improve_algorithm = improve_algorithm
            improve_algorithm = temp_override(improver_str, "improve_algorithm")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume_from", type=str, default=None)
    parser.add_argument("--resume_from_last", action="store_true")
    args = parser.parse_args()

    resume_from = args.resume_from
    if args.resume_from_last:
        # Loop over the ints at the start of the run IDs
        run_ids = [f for f in os.listdir("results")]
        run_ids = [f for f in run_ids if f[0].isdigit()]
        run_ids = sorted(run_ids, key=lambda x: int(x.split("_")[0]))
        run_id = run_ids[-1]
        resume_from = run_id
    if resume_from is not None:
        run_id = resume_from
    else:
        run_id = generate_run_id(
            config["iterative"], use_seed_algorithm, config["use_improver"], config["subtask"]
        )
        # Create a folder for the results
        os.makedirs(f"results/{run_id}", exist_ok=True)
    run_improver_main()