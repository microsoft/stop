from algorithm import algorithm_str
from task_utility import utility
from language_model import LanguageModel

def meta_utility(improve_str: str):
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
            exec(improve_str, globals())  # Define improve_algorithm function
        except:
            continue
        # At most 4 calls to language model, and at most 6 samples each time
        language_model = LanguageModel(budget=4, max_responses_per_call=6)
        improved_algorithm_str = improve_algorithm(algorithm_str, utility, language_model)
        expected_utility += utility(improved_algorithm_str) / n_tests

    return expected_utility