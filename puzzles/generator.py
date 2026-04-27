from __future__ import annotations
from typing import Literal

import numpy as np
from core.csp import SudokuCSP


# Difficulty settings: percentage of cells to remove
DIFFICULTY_SETTINGS = {
    'Easy': 0.37,    # ~35-40% of cells removed
    'Medium': 0.47,  # ~45-50% of cells removed
    'Hard': 0.57,    # ~55-60% of cells removed
}

DifficultyType = Literal['Easy', 'Medium', 'Hard']


def generate_puzzle(size: int = 9, difficulty: str = 'Easy') -> list[list[int]]:
    box_size = int(np.sqrt(size))
    if box_size * box_size != size:
        raise ValueError(f"Size must be a perfect square, got {size}")
    
    # Start with empty board
    board: list[list[int]] = [[0 for _ in range(size)] for _ in range(size)]
    
    # Fill diagonal boxes first (they don't constrain each other)
    for box_num in range(box_size):
        nums = list(range(1, size + 1))
        np.random.shuffle(nums)
        idx = 0
        for r in range(box_size):
            for c in range(box_size):
                board[box_num * box_size + r][box_num * box_size + c] = nums[idx]
                idx += 1
    
    # Solve to get a complete valid board
    temp_csp = SudokuCSP(size, board)
    gen = temp_csp.backtrack_generator()
    solution: dict[tuple[int, int], int] | None = None
    
    for event in gen:
        if event[0] == 'solution':
            solution = event[1]
            break
    
    if solution:
        # Create complete board from solution
        for r in range(size):
            for c in range(size):
                if (r, c) in solution:
                    board[r][c] = solution[(r, c)]
        
        # Remove numbers based on difficulty
        cells_to_remove = _get_cells_to_remove(difficulty, size)
        
        cells = [(r, c) for r in range(size) for c in range(size)]
        np.random.shuffle(cells)
        
        for i in range(min(cells_to_remove, len(cells))):
            r, c = cells[i]
            board[r][c] = 0
    
    return board


def _get_cells_to_remove(difficulty: str, size: int) -> int:
    total_cells = size * size
    percentage = DIFFICULTY_SETTINGS.get(difficulty, DIFFICULTY_SETTINGS['Easy'])
    return int(total_cells * percentage)


def is_valid_puzzle(board: list[list[int]], max_iterations: int = 200000) -> bool:
    """
    Check if a puzzle is valid (has exactly one solution).
    
    Args:
        board: 2D list representing the puzzle
        max_iterations: Maximum iterations before giving up (default 200k)
    
    Returns:
        True if puzzle has exactly one solution, False if no solution,
        multiple solutions, or max_iterations exceeded
    """
    if not board or not board[0]:
        return False
    
    size = len(board)
    
    # Validate dimensions
    if any(len(row) != size for row in board):
        return False
    
    csp = SudokuCSP(size, board)
    
    # Quick check: if any variable has empty initial domain, puzzle is unsolvable
    for var in csp.variables:
        if not csp.initial_domains.get(var):
            return False
    
    solution_count = 0
    gen = csp.backtrack_generator()
    
    for i, event in enumerate(gen):
        if i > max_iterations:
            return False  # Too complex, give up
        if event[0] == 'solution':
            solution_count += 1
            if solution_count > 1:
                return False  # Multiple solutions
    
    return solution_count == 1  # Exactly one solution