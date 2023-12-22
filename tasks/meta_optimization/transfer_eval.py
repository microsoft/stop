from pebble import ThreadPool
import numpy as np
import os
import time
import jsonlines
import traceback
from language_model import LanguageModel
from tqdm import tqdm

from config import config
from helpers import (
    read_file_as_str, generate_seed_algorithm, write_str_to_file,
    temp_override
)

# Suppress warnings
import warnings
warnings.filterwarnings("ignore")

start_time = time.time()
subtasks = ['three_sat']
print(subtasks)
for subtask in subtasks:
    print("=====================================")
    print("subtask:", subtask)
    if subtask == "meta_optimization":
        continue
    # print the current directory
    base_secret_utility_str = read_file_as_str(f"tasks/{subtask}/secret_utility.py")
    base_utility_str = read_file_as_str(f"tasks/{subtask}/utility.py")
    try:
        base_algorithm_str = read_file_as_str(f"tasks/{subtask}/seed_algorithm.py")
    except:
        base_algorithm_str = generate_seed_algorithm(base_utility_str)
        write_str_to_file(base_algorithm_str, f"tasks/{subtask}/seed_algorithm.py")

    def get_improver(improve_str: str, utility, mode: str = "val", language_model=None):
        """
        Uses the improvement algorithm in improve_str to improve the algorithm in algorithm_str, according to the utility function.
        """
        try:
            print("DEFINING ALGORITHM META")
            new_improve_algorithm = temp_override(improve_str, "improve_algorithm")
            print("DEFINED ALGORITHM META")
        except Exception as e:
            print("Definition failed with exception:", e)
            print(traceback.format_exc())
            raise e
        try:
            print("Improver:")
            print(improve_str)
            print("Base algorithm:")
            print(base_algorithm_str)
            improved_algorithm_str = new_improve_algorithm(base_algorithm_str, utility, language_model)
            print("Improved algorithm:")
            print(improved_algorithm_str)
            return improved_algorithm_str
        except Exception as e:
            print("=====================================")
            print("Improver failed with exception:", e)
            print(traceback.format_exc())
            print("Improver:")
            print(improve_str)
            print("=====================================")
            raise e

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

        if use_timeout:
            pool = ThreadPool()
        improved_algorithm_futures = []
        improved_algorithm_strs = []
        if use_timeout:
            if use_parallel:
                for test_idx in range(n_tests):
                    language_model = LanguageModel(budget=config['language_model_call_budget'])
                    utility.uses = 0
                    improved_algorithm_future = pool.schedule(get_improver, (improve_str, utility, mode, language_model))
                    improved_algorithm_futures.append(improved_algorithm_future)
                for improved_algorithm_future in improved_algorithm_futures:
                    try:
                        timeout = 60 * 60
                        improved_algorithm_str = improved_algorithm_future.result(timeout=timeout)
                    except Exception as e:
                        print("Exception in improving algorithm in utility:", e)
                        print(traceback.format_exc())
                        improved_algorithm_str = ""
                        if not handle_exceptions:
                            raise e
                        if not log_usage:
                            return 0
                    improved_algorithm_strs.append(improved_algorithm_str)
            else:
                for test_idx in tqdm(range(n_tests)):
                    language_model = LanguageModel(budget=config['language_model_call_budget'])
                    utility.uses = 0
                    improved_algorithm_future = pool.schedule(get_improver, (improve_str, utility, mode, language_model))
                    try:
                        timeout = 60 * 60
                        improved_algorithm_str = improved_algorithm_future.result(timeout=timeout)
                    except Exception as e:
                        print("Exception in improving algorithm in utility:", e)
                        print(traceback.format_exc())
                        improved_algorithm_str = ""
                        if not handle_exceptions:
                            raise e
                        if not log_usage:
                            return 0
                    improved_algorithm_strs.append(improved_algorithm_str)
        else:
            for test_idx in tqdm(range(n_tests)):
                language_model = LanguageModel(budget=config['language_model_call_budget'])
                utility.uses = 0
                try:
                    improved_algorithm_str = get_improver(improve_str, utility, mode, language_model)
                except Exception as e:
                    print("Exception in improving algorithm in utility:", e)
                    print(traceback.format_exc())
                    improved_algorithm_str = ""
                    if not handle_exceptions:
                        raise e
                    if not log_usage:
                        return 0
                improved_algorithm_strs.append(improved_algorithm_str)
        if use_timeout:
            pool.stop()
        # pool.join()
        for test_idx, improved_algorithm_str in enumerate(improved_algorithm_strs):
            if not improved_algorithm_str:
                continue
            # Save the improved algorithm to a file
            # First, find the most recent folder in results
            # Then, save the algorithm to that folder
            time_elapsed = int(eval_idx) - int(run_id.split("_")[0])
            write_str_to_file(base_algorithm_str, f"results/{run_id}/base_algorithm_{time_elapsed}_{test_idx}.py")
            write_str_to_file(improved_algorithm_str, f"results/{run_id}/improved_algorithm_{time_elapsed}_{test_idx}.py")
            print("Evaluating improved algorithm on val")
            try:
                utility.uses = 0
                new_utility_val = utility(improved_algorithm_str, mode=mode)
            except Exception as e:
                print("Exception in evaluating improved algorithm val in metautil:", e)
                print(traceback.format_exc())
                new_utility_val = 0
                if not handle_exceptions:
                    raise e
                if not log_usage:
                    return 0
            expected_utility_val += new_utility_val / n_tests
            # Also log test
            if log_usage:
                print("Evaluating improved algorithm on test")
                try:
                    utility.uses = 0
                    new_utility_test = utility(improved_algorithm_str, mode="test")
                except Exception as e:
                    print("Exception in evaluating improved algorithm test in metautil:", e)
                    print(traceback.format_exc())
                    new_utility_test = 0
                    if not handle_exceptions:
                        raise e
                    if not log_usage:  # Just in case we end up getting rid of that if above...
                        return 0
                expected_utility_test += new_utility_test / n_tests
            # Write the utility value to a file
            cur_time = time.time()
            base_save_filename = f"meta_utility_{start_time}_{cur_time}.jsonl"
            if config['transfer_eval_type'] == 'base':
                save_filename = 'base' + base_save_filename
            else:
                save_filename = 'improved' + base_save_filename
                
            with jsonlines.open(save_filename, mode="a") as writer:
                writer.write({"task": subtask, "utility": new_utility_val, "utility_test": new_utility_test})
        print("Expected utility val:", expected_utility_val)
        if log_usage:
            print("Expected utility test:", expected_utility_test)

        return expected_utility_val, expected_utility_test


    # We're in secret_utility.py - we want the string of utility.py
    fake_self_str = read_file_as_str(f"tasks/{config['task']}/utility.py")
    meta_utility.budget = config['meta_utility_budget']
    meta_utility.str = fake_self_str

    if config['transfer_eval_type'] == 'base':
        improve_algorithm_path = "tasks/meta_optimization/secret_seed_algorithm.py"
    else:
        improve_algorithm_base = "tasks/meta_optimization/secret_seed_algorithm_improved.py"
    with open(improve_algorithm_path, 'r') as file:
        improve_algorithm_str = file.read()
    
    util_val, util_test = meta_utility(improve_algorithm_str, log_usage=True, handle_exceptions=True)