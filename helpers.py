from language_model import LanguageModel
import os
import time
import traceback
import importlib
import platform
import faulthandler

def extract_code(algorithm_str):
    if isinstance(algorithm_str, str):
        # If the result is wrapped in triple backticks, remove the first and last lines
        return find_largest_code_block_line_by_line(algorithm_str)
    elif isinstance(algorithm_str, list):
        extracted_codes = [extract_code(algorithm_str) for algorithm_str in algorithm_str]
        return extracted_codes

def find_largest_code_block_line_by_line(text):
    largest_block = ""
    current_block = ""
    nesting_level = 0  # To keep track of the level of nesting

    lines = text.split("\n")
    
    for line in lines:
        if line.startswith("```"):  # We've found a block delimiter
            if not line[3:].strip():  # If it's a closing delimiter
                nesting_level -= 1  # Decrease the nesting level
                
                if nesting_level == 0:  # We've closed the outermost block
                    current_block += line + "\n"  # Add the line to the current block
                    
                    # Compare the length of the current block with the largest block found so far
                    if len(current_block) > len(largest_block):
                        largest_block = current_block
                    
                    current_block = ""  # Reset the current block
                else:
                    current_block += line + "\n"  # Add the line to the current block
            else:  # It's an opening delimiter
                current_block += line + "\n"  # Add the line to the current block
                nesting_level += 1  # Increase the nesting level
        else:
            if nesting_level > 0:  # If we're inside a block
                current_block += line + "\n"  # Add the line to the current block

    if largest_block:
        # Remove the first and last lines (the outermost backticks)
        largest_block = "\n".join(largest_block.strip().split("\n")[1:-1])

    return largest_block if largest_block else None

def run_by_creating_file(define_fn_str, base_name):
    # Create a file with the define_fn_str
    timestamp = str(time.time()).replace(".", "")
    # Make the temp directory if it doesn't exist
    os.makedirs("temp", exist_ok=True)
    write_str_to_file(define_fn_str, f"temp/{base_name}_{timestamp}.py")
    # Import the file
    imported = False
    attempts = 0
    while not imported and attempts < 10:
        try:
            importlib.invalidate_caches()
            module = importlib.import_module(f"temp.{base_name}_{timestamp}")
            imported = True
        except ModuleNotFoundError as e:
            print("Module not found, trying again")
            print("Exception:", e)
            time.sleep(0.1)
            attempts += 1
        except Exception as e:
            print("Failed to import module with exception", e)
            print(traceback.format_exc())
            raise e
    # Get the function
    fn = getattr(module, base_name)
    return fn


def reliability_guard(maximum_memory_bytes = None):
    """
    Based on humaneval sandbox - slightly less restrictive:
    https://github.com/openai/human-eval/blob/master/human_eval/execution.py

    This disables various destructive functions and prevents the generated code
    from interfering with the test (e.g. fork bomb, killing other processes,
    removing filesystem files, etc.)

    WARNING
    This function is NOT a security sandbox. Untrusted code, including, model-
    generated code, should not be blindly executed outside of one. See the 
    Codex paper for more information about OpenAI's code sandbox, and proceed
    with caution.
    """

    if maximum_memory_bytes is not None:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (maximum_memory_bytes, maximum_memory_bytes))
        resource.setrlimit(resource.RLIMIT_DATA, (maximum_memory_bytes, maximum_memory_bytes))
        if not platform.uname().system == 'Darwin':
            resource.setrlimit(resource.RLIMIT_STACK, (maximum_memory_bytes, maximum_memory_bytes))

    faulthandler.disable()

    import builtins
    builtins.exit = None
    builtins.quit = None

    os.kill = None
    os.system = None
    # os.putenv = None
    os.remove = None
    os.removedirs = None
    os.rmdir = None
    os.fchdir = None
    os.setuid = None
    os.fork = None
    os.forkpty = None
    os.killpg = None
    os.rename = None
    os.renames = None
    os.truncate = None
    os.replace = None
    os.unlink = None
    os.fchmod = None
    os.fchown = None
    os.chmod = None
    os.chown = None
    os.chroot = None
    os.fchdir = None
    os.lchflags = None
    os.lchmod = None
    os.lchown = None
    os.getcwd = None
    os.chdir = None

    import shutil
    shutil.rmtree = None
    shutil.move = None
    shutil.chown = None

    # import subprocess
    # subprocess.Popen = None  # type: ignore

    __builtins__['help'] = None

    import sys
    sys.modules['ipdb'] = None
    # sys.modules['joblib'] = None
    sys.modules['resource'] = None
    sys.modules['psutil'] = None
    sys.modules['tkinter'] = None

def temp_override(define_fn_str, base_name, update_globals=True, use_sandbox=True, strict_sandbox=True):
    """
    Overrides a function temporarily.
    """
    if define_fn_str is None:
        raise Exception("define_fn_str is None in temp_override")
    if use_sandbox:
        filtered_strings = ['ProcessPool']
        for filtered_str in filtered_strings:
            if filtered_str in define_fn_str:
                raise Exception(f"{filtered_str} is not supported in temp_override")
        if strict_sandbox:
            if not os.path.exists("acknowledge_strict_sandbox.txt"):
                print("WARNING: Although this script mode is less likely to crash your computer, it is still not a true sandbox and may cause your computer to crash. You should not run this script anywhere where you would not allow a stranger to run arbitrary code.")
                acknowledge_strict_sandbox = input("Confirm that you acknowledge this (y/n): ")
                if acknowledge_strict_sandbox != "y":
                    raise Exception("Aborting due to sandbox warning")
                else:
                    write_str_to_file("", "acknowledge_strict_sandbox.txt")
            reliability_guard()
        else:
            if not os.path.exists("acknowledge_unsafe.txt"):
                print("WARNING: You are using temp_override without a strict sandbox. This is particularly unsafe and may cause your computer to crash.")
                acknowledge_unsafe = input("Confirm that you acknowledge this (y/n): ")
                if acknowledge_unsafe != "y":
                    raise Exception("Aborting due to sandbox warning")
                else:
                    write_str_to_file("", "acknowledge_unsafe.txt")
                

    new_globals = globals().copy()
    if base_name in new_globals:
        del new_globals[base_name]
    new_fn = run_by_creating_file(define_fn_str, base_name)  # Useful for debugging
    if base_name in new_globals:
        del new_globals[base_name]
    if update_globals:
        globals().update(new_globals)
    return new_fn

def read_file_as_str(path):
    with open(path, "r") as f:
        return f.read()

def write_str_to_file(s, path, mode="w"):
    if isinstance(s, list):
        s = "\n\n".join(s)
    try:
        with open(path, mode) as f:
            f.write(s)
    except Exception as e:
        print("Failed to write to file", path, "with exception", e)
        print("Traceback:", traceback.format_exc())
        s = str(s)
        with open(path, mode) as f:
            f.write(s)

def generate_seed_algorithm(utility_str, t=0.7):
    """
    Implements an algorithm according to a utility function.
    """
    role = "You are an expert programmer, especially skilled at implementing algorithms."
    message = f"""You must write a script that will implement a Python algorithm to solve a problem as well as possible.

You will be evaluated based on the following utility function:
```python
{utility_str}
```
"""
    language_model = LanguageModel(budget=1)
    algorithm_str = language_model.prompt(role, message, n_responses=1, temperature=t)[0]
    algorithm_str = extract_code(algorithm_str)
    return algorithm_str

def generate_run_id(iterative, use_seed_algorithm, use_improver, SUBTASK):
    """
    Generates a unique run ID for a run.
    """
    run_id = str(int(time.time()))
    if iterative:
        run_id += "_iterative"
    if use_seed_algorithm:
        run_id += "_seed"
    if use_improver:
        run_id += "_improver"
    run_id += f"_{SUBTASK}"
    return run_id

def load_seed_algorithm(task, utility_str, use_existing=False):
    """
    Gets the seed algorithm for a task.
    """
    seed_algorithm_path = f"tasks/{task}/seed_algorithm.py"
    if use_existing and not os.path.exists(seed_algorithm_path):
        seed_algorithm_str = generate_seed_algorithm(utility_str)
        write_str_to_file(seed_algorithm_str, seed_algorithm_path)
    if use_existing:
        return read_file_as_str(seed_algorithm_path)
    return seed_algorithm_str

def get_utility_strs(task):
    """
    Gets the utility function for a task.
    """
    return read_file_as_str(f"tasks/{task}/utility.py"), read_file_as_str(f"tasks/{task}/secret_utility.py")

def end_pool_if_used(pool, join_pools=False):
    """
    Ends a pool if it is used.
    """
    if pool is not None:
        pool.stop()
        if join_pools:
            pool.join()

def write_log(expected_utility_val, expected_utility_test, run_id):
    """
    Writes the expected utility to a log file.
    """
    print("Saving to file")
    with open(f"results/{run_id}/meta_utility_log.txt", "a") as f:
        f.write(f"{expected_utility_val},{expected_utility_test}\n")
