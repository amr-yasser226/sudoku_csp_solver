from __future__ import annotations
from typing import Iterator
import numpy as np


class SudokuCSP:
    
    def __init__(self, size: int = 9, initial_board: list[list[int]] | None = None) -> None:
        self.size = size
        self.box_size = int(np.sqrt(size))  # 3 for 9x9 Sudoku
        
        if self.box_size * self.box_size != size:
            raise ValueError(f"Size must be a perfect square, got {size}")
        
        # Variables are (row, col) tuples for empty cells
        self.variables: list[tuple[int, int]] = []
        self.initial_domains: dict[tuple[int, int], list[int]] = {}
        
        # Initialize board
        if initial_board is None:
            self.initial_board = [[0 for _ in range(size)] for _ in range(size)]
        else:
            self.initial_board = [row[:] for row in initial_board]
        
        # Set up variables and domains
        for r in range(size):
            for c in range(size):
                if self.initial_board[r][c] == 0:
                    self.variables.append((r, c))
                    self.initial_domains[(r, c)] = list(range(1, size + 1))
        
        # Remove values that conflict with initial assignments
        for r in range(size):
            for c in range(size):
                if self.initial_board[r][c] != 0:
                    val = self.initial_board[r][c]
                    self._remove_conflicts(r, c, val, self.initial_domains)
        
        self.reset()
    
    def _remove_conflicts(
        self, 
        row: int, 
        col: int, 
        value: int, 
        domains: dict[tuple[int, int], list[int]]
    ) -> None:
        for (r, c) in list(domains.keys()):
            if r == row or c == col or (r // self.box_size == row // self.box_size and 
                                        c // self.box_size == col // self.box_size):
                if value in domains[(r, c)]:
                    domains[(r, c)].remove(value)
    
    def reset(self) -> None:
        """Reset solver statistics."""
        self.nodes: int = 0
        self.backtracks: int = 0
        self.solutions: int = 0
    
    def is_consistent(
        self, 
        var: tuple[int, int], 
        value: int, 
        assignment: dict[tuple[int, int], int]
    ) -> bool:
        row, col = var
        
        # Check row constraint
        for c in range(self.size):
            if (row, c) in assignment and assignment[(row, c)] == value:
                return False
        
        # Check column constraint
        for r in range(self.size):
            if (r, col) in assignment and assignment[(r, col)] == value:
                return False
        
        # Check box constraint
        box_row = (row // self.box_size) * self.box_size
        box_col = (col // self.box_size) * self.box_size
        for r in range(box_row, box_row + self.box_size):
            for c in range(box_col, box_col + self.box_size):
                if (r, c) in assignment and assignment[(r, c)] == value:
                    return False
        
        return True
    
    # MRV heuristic
    def select_unassigned_var(
        self, 
        domains: dict[tuple[int, int], list[int]], 
        assignment: dict[tuple[int, int], int]
    ) -> tuple[int, int]:
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: (len(domains[v]), -self._count_constraints(v, assignment)))
    
    def _count_constraints(
        self, 
        var: tuple[int, int], 
        assignment: dict[tuple[int, int], int]
    ) -> int:
        row, col = var
        count = 0
        for (r, c) in self.variables:
            if (r, c) not in assignment and (r, c) != var:
                if r == row or c == col or (r // self.box_size == row // self.box_size and 
                                            c // self.box_size == col // self.box_size):
                    count += 1
        return count
    
    # LCV heuristic
    def order_domain_values(
        self, 
        var: tuple[int, int], 
        domains: dict[tuple[int, int], list[int]], 
        assignment: dict[tuple[int, int], int]
    ) -> list[int]:
        def eliminated_count(value: int) -> int:
            count = 0
            row, col = var
            for (r, c) in self.variables:
                if (r, c) == var or (r, c) in assignment:
                    continue
                if (r == row or c == col or (r // self.box_size == row // self.box_size and 
                                             c // self.box_size == col // self.box_size)):
                    if value in domains[(r, c)]:
                        count += 1
            return count
        
        values = list(domains[var])
        values.sort(key=eliminated_count)
        return values
    
    def forward_check(
        self, 
        var: tuple[int, int], 
        value: int, 
        domains: dict[tuple[int, int], list[int]]
    ) -> tuple[dict[tuple[int, int], list[int]] | None, dict[tuple[int, int], list[int]]]:
        new_domains = {v: list(domains[v]) for v in domains}
        removed: dict[tuple[int, int], list[int]] = {v: [] for v in domains}
        new_domains[var] = [value]
        
        row, col = var
        
        # Remove value from all cells in same row, column, and box
        for (r, c) in self.variables:
            if (r, c) == var:
                continue
            
            if r == row or c == col or (r // self.box_size == row // self.box_size and 
                                        c // self.box_size == col // self.box_size):
                if value in new_domains[(r, c)]:
                    new_domains[(r, c)].remove(value)
                    removed[(r, c)].append(value)
                
                # If domain becomes empty, forward checking fails
                if not new_domains[(r, c)]:
                    return None, removed
        
        return new_domains, removed
    
    def backtrack_generator(
        self, 
        domains: dict[tuple[int, int], list[int]] | None = None, 
        assignment: dict[tuple[int, int], int] | None = None
    ) -> Iterator[tuple[str, ...]]:
        if domains is None:
            domains = {v: list(self.initial_domains[v]) for v in self.variables}
        if assignment is None:
            assignment = {}
        
        self.nodes += 1
        
        # Check if all variables are assigned
        if len(assignment) == len(self.variables):
            self.solutions += 1
            yield ('solution', dict(assignment))
            return
        
        # Select unassigned variable using MRV
        var = self.select_unassigned_var(domains, assignment)
        yield ('mrv', var, domains[var])
        
        # Order domain values using LCV
        lcv_order = self.order_domain_values(var, domains, assignment)
        yield ('lcv', var, lcv_order)
        
        # Try each value in order
        for value in lcv_order:
            # Check consistency
            if not self.is_consistent(var, value, assignment):
                yield ('pruned', var, value)
                continue
            
            # Assign value
            assignment[var] = value
            yield ('assign', var, value, dict(assignment))
            
            # Forward checking
            fc = self.forward_check(var, value, domains)
            if fc[0] is None:
                # Forward checking failed - domain wipeout
                yield ('fc_fail', var, value, fc[1])
                del assignment[var]
                self.backtracks += 1
                yield ('unassign', var, dict(assignment))
                continue
            
            new_domains, removed = fc
            yield ('fc_ok', var, value, removed)
            
            # Recursively solve
            yield from self.backtrack_generator(new_domains, assignment)
            
            # Backtrack
            del assignment[var]
            self.backtracks += 1
            yield ('unassign', var, dict(assignment))