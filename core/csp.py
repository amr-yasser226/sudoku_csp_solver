"""
Core Sudoku CSP Solver
Implements backtracking search with:
- MRV (Minimum Remaining Values) heuristic
- LCV (Least Constraining Value) heuristic
- Forward Checking constraint propagation
"""

import numpy as np


class SudokuCSP:
    """
    Constraint Satisfaction Problem solver for Sudoku.
    
    Variables: Empty cells represented as (row, col) tuples
    Domains: Numbers 1-9 for each empty cell
    Constraints: No duplicates in row, column, or 3x3 box
    """
    
    def __init__(self, size=9, initial_board=None):
        """
        Initialize Sudoku CSP solver.
        
        Args:
            size: Board size (9 for standard 9x9 Sudoku)
            initial_board: 2D list with 0 for empty cells, 1-9 for filled cells
        """
        self.size = size
        self.box_size = int(np.sqrt(size))  # 3 for 9x9 Sudoku
        
        # Variables are (row, col) tuples for empty cells
        self.variables = []
        self.initial_domains = {}
        
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
    
    def _remove_conflicts(self, row, col, value, domains):
        """
        Remove value from domains of cells in same row, column, and box.
        
        Args:
            row: Row index
            col: Column index
            value: Value to remove
            domains: Domain dictionary to update
        """
        for (r, c) in list(domains.keys()):
            if r == row or c == col or (r // self.box_size == row // self.box_size and 
                                        c // self.box_size == col // self.box_size):
                if value in domains[(r, c)]:
                    domains[(r, c)].remove(value)
    
    def reset(self):
        """Reset solver statistics"""
        self.nodes = 0
        self.backtracks = 0
        self.solutions = 0
    
    def is_consistent(self, var, value, assignment):
        """
        Check if assigning value to var is consistent with current assignment.
        
        Args:
            var: Variable (row, col) tuple
            value: Value to assign
            assignment: Current assignment dictionary
            
        Returns:
            True if consistent, False otherwise
        """
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
    
    def select_unassigned_var(self, domains, assignment):
        """
        Select next variable using MRV (Minimum Remaining Values) heuristic.
        Ties broken by degree (most constraining variable).
        
        Args:
            domains: Current domain dictionary
            assignment: Current assignment dictionary
            
        Returns:
            Variable (row, col) tuple with smallest domain
        """
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: (len(domains[v]), -self._count_constraints(v, assignment)))
    
    def _count_constraints(self, var, assignment):
        """
        Count how many unassigned variables this variable constrains.
        Used for degree heuristic tie-breaking.
        
        Args:
            var: Variable (row, col) tuple
            assignment: Current assignment dictionary
            
        Returns:
            Number of constraints
        """
        row, col = var
        count = 0
        for (r, c) in self.variables:
            if (r, c) not in assignment and (r, c) != var:
                if r == row or c == col or (r // self.box_size == row // self.box_size and 
                                            c // self.box_size == col // self.box_size):
                    count += 1
        return count
    
    def order_domain_values(self, var, domains, assignment):
        """
        Order domain values using LCV (Least Constraining Value) heuristic.
        Values that rule out fewer choices for neighbors are tried first.
        
        Args:
            var: Variable (row, col) tuple
            domains: Current domain dictionary
            assignment: Current assignment dictionary
            
        Returns:
            Ordered list of values to try
        """
        def eliminated_count(value):
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
    
    def forward_check(self, var, value, domains):
        """
        Apply forward checking: remove inconsistent values from neighboring domains.
        
        Args:
            var: Variable (row, col) tuple
            value: Value being assigned
            domains: Current domain dictionary
            
        Returns:
            (new_domains, removed) tuple where:
                - new_domains is updated domains dict (or None if failure)
                - removed is dict of values removed from each domain
        """
        new_domains = {v: list(domains[v]) for v in domains}
        removed = {v: [] for v in domains}
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
    
    def backtrack_generator(self, domains=None, assignment=None):
        """
        Backtracking search with generator for step-by-step visualization.
        Yields events that can be consumed by the GUI for visualization.
        
        Args:
            domains: Current domain dictionary (or None to use initial)
            assignment: Current assignment dictionary (or None for empty)
            
        Yields:
            Tuples representing events: ('event_type', data...)
        """
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
            for e in self.backtrack_generator(new_domains, assignment):
                yield e
            
            # Backtrack
            del assignment[var]
            self.backtracks += 1
            yield ('unassign', var, dict(assignment))