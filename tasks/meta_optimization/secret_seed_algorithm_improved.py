from helpers import extract_code

def improve_algorithm(initial_solution, utility, language_model):
    """Improves a solution according to a utility function."""
    expertise = "You are an expert computer science researcher and programmer, especially skilled at optimizing algorithms."
    
    n_messages = min(language_model.max_responses_per_call, utility.budget)
    temperature_values = [0.4, 0.7, 1.0]
    solutions_cache = set()
    new_solutions = []
    utility_cache = {}

    def evaluate_solution(solution):
        if solution not in utility_cache:
            utility_cache[solution] = utility(solution)
        return utility_cache[solution]

    for temp in temperature_values:
        base_message =  f"""Improve the following solution:
```python
{initial_solution}
```

You will be evaluated based on this score function:
```python
{utility.str}
```

You must return an improved solution. Be as creative as you can under the constraints.
Your primary improvement must be novel and non-trivial. Generate a solution with temperature={temp} that focuses on different aspects of optimization."""
        
        generated_solutions = language_model.batch_prompt(expertise, [base_message] * n_messages, temperature=temp)
        generated_solutions = extract_code(generated_solutions)
        
        # Evaluate and sort the generated solutions by their utility score
        scored_solutions = [(sol, evaluate_solution(sol)) for sol in generated_solutions if sol not in solutions_cache]
        scored_solutions.sort(key=lambda x: x[1], reverse=True)
        
        # Keep only the top n_messages solutions
        top_solutions = scored_solutions[:n_messages]
        
        for sol, _ in top_solutions:
            new_solutions.append(sol)
            solutions_cache.add(sol)

    # Dynamically adjust temperature values based on the utility scores
    temperature_values = [temp * (1 + evaluate_solution(sol) / evaluate_solution(initial_solution)) for temp, sol in zip(temperature_values, new_solutions)]

    best_solution = max(new_solutions, key=evaluate_solution)
    return best_solution