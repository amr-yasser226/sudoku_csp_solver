from __future__ import annotations
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.csp import SudokuCSP


def arc_consistency_3(
    csp: SudokuCSP, 
    domains: dict[tuple[int, int], list[int]],
    var: tuple[int, int] | None = None
) -> bool:
    # Create queue of all arcs
    queue: deque[tuple[tuple[int, int], tuple[int, int]]] = deque()
    
    if var is None:
        # Add all arcs
        for v1 in csp.variables:
            for v2 in csp.variables:
                if v1 != v2 and are_neighbors(v1, v2, csp.box_size):
                    queue.append((v1, v2))
    else:
        # Add arcs from var to all neighbors
        for v2 in csp.variables:
            if v2 != var and are_neighbors(var, v2, csp.box_size):
                queue.append((var, v2))
    
    while queue:
        (xi, xj) = queue.popleft()
        
        if _revise(domains, xi, xj):
            if len(domains[xi]) == 0:
                return False
            
            # Add arcs from neighbors of xi
            for xk in csp.variables:
                if xk != xi and xk != xj and are_neighbors(xk, xi, csp.box_size):
                    queue.append((xk, xi))
    
    return True


def _revise(
    domains: dict[tuple[int, int], list[int]], 
    xi: tuple[int, int], 
    xj: tuple[int, int]
) -> bool:
    revised = False
    
    for x in list(domains[xi]):
        # Check if there's any value in xj's domain that satisfies constraint
        found = False
        for y in domains[xj]:
            if x != y:  # Different values satisfy Sudoku constraint
                found = True
                break
        
        if not found:
            domains[xi].remove(x)
            revised = True
    
    return revised


def are_neighbors(var1: tuple[int, int], var2: tuple[int, int], box_size: int) -> bool:
    r1, c1 = var1
    r2, c2 = var2
    
    # Same row
    if r1 == r2:
        return True
    
    # Same column
    if c1 == c2:
        return True
    
    # Same box
    if (r1 // box_size == r2 // box_size and 
        c1 // box_size == c2 // box_size):
        return True
    
    return False


def solve_with_ac3(csp: SudokuCSP) -> dict[tuple[int, int], int] | None:
    # Create a copy of domains for AC-3
    domains = {v: list(csp.initial_domains[v]) for v in csp.variables}
    
    # Apply AC-3 first to reduce search space
    if not arc_consistency_3(csp, domains):
        return None
    
    # Then use regular backtracking with reduced domains
    for event in csp.backtrack_generator(domains=domains):
        if event[0] == 'solution':
            return event[1]
    
    return None


def count_solutions(csp: SudokuCSP, max_count: int = 2) -> int:
    count = 0
    
    for event in csp.backtrack_generator():
        if event[0] == 'solution':
            count += 1
            if count >= max_count:
                break
    
    return count


def get_hint(
    csp: SudokuCSP, 
    current_assignment: dict[tuple[int, int], int]
) -> tuple[tuple[int, int], int] | None:
    # Find unassigned variable with smallest domain
    unassigned = [v for v in csp.variables if v not in current_assignment]
    
    if not unassigned:
        return None
    
    # Get domains for current state
    domains: dict[tuple[int, int], list[int]] = {
        v: list(csp.initial_domains[v]) for v in csp.variables
    }
    
    # Apply forward checking for current assignments
    for var, val in current_assignment.items():
        fc, _ = csp.forward_check(var, val, domains)
        if fc:
            domains = fc
    
    # Select variable with smallest domain
    best_var = min(unassigned, key=lambda v: len(domains[v]))
    
    if not domains[best_var]:
        return None
    
    # Return first value in domain (could use LCV here)
    return (best_var, domains[best_var][0])