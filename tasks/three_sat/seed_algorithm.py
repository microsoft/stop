import random

def random_walk_solver(formula, max_iter, p):
    n = max(abs(lit) for clause in formula for lit in clause)
    assignments = [False] * (n + 1)
    
    for _ in range(max_iter):
        unsatisfied_clauses = [clause for clause in formula if not any(assignments[abs(lit)] == (lit > 0) for lit in clause)]
        
        if not unsatisfied_clauses:
            return assignments
        
        clause_to_flip = random.choice(unsatisfied_clauses)
        if random.random() < p:
            lit_to_flip = random.choice(clause_to_flip)
        else:
            lit_to_flip = min(clause_to_flip, key=lambda lit: sum(assignments[abs(lit)] == (lit > 0) for clause in formula if lit in clause))
        
        assignments[abs(lit_to_flip)] = not assignments[abs(lit_to_flip)]
    
    return None

def algorithm(formula):
    return random_walk_solver(formula, max_iter=1000, p=0.4)