from algorithm import algorithm_str
from task_utility import utility
from language_model import LanguageModel
from run import run

def meta_utility(improve_str: str, use_sandbox: bool):
    """
    Evaluates the algorithm in improve_str to improve the algorithm in algorithm_str, according to
    some downstream utility function. This meta-utility function can only be called 25 times.
    """
    if meta_utility.uses > meta_utility.budget:
        return 0
    meta_utility.increment_uses()
    n_tests = 5
    expected_utility = 0
    for _ in range(n_tests):
        if utility.uses >= utility.budget:
            break
        try:
            run(improve_str, globals(), use_sandbox=use_sandbox)  # Define improve_algorithm function
        except:
            continue
        # At most 5 calls to language model, and at most 5 samples each time
        language_model = LanguageModel(budget=5, max_responses_per_call=5)
        improved_algorithm_str = improve_algorithm(algorithm_str, utility, language_model)
        expected_utility += utility(improved_algorithm_str, use_sandbox=use_sandbox) / n_tests

    return expected_utility