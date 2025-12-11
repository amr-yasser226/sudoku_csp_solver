"""
Sudoku puzzle generator
Creates random solvable puzzles of varying difficulty
"""

import numpy as np
from core.csp import SudokuCSP


def generate_puzzle(size=9, difficulty='Easy'):
    """
    Generate a random solvable Sudoku puzzle.
    """
    box_size = int(np.sqrt(size))
    
    # empty board for the start
    board = [[0 for _ in range(size)] for _ in range(size)]
    
    # diagonal boxes first
    for box_num in range(box_size):
        nums = list(range(1, size + 1))
        np.random.shuffle(nums)
        idx = 0
        for r in range(box_size):
            for c in range(box_size):
                board[box_num * box_size + r][box_num * box_size + c] = nums[idx]
                idx += 1
    
    temp_csp = SudokuCSP(size, board)
    gen = temp_csp.backtrack_generator()
    solution = None
    for event in gen:
        if event[0] == 'solution':
            solution = event[1]
            break
    
    if solution:
        # Create a complete board
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


def _get_cells_to_remove(difficulty, size):
    """
    Determine how many cells to remove based on difficulty.
    
    Returns: number of cells to remove
    """
    total_cells = size * size
    
    if difficulty == 'Easy':
        # about 35-40% of cells
        return int(total_cells * 0.37)
    elif difficulty == 'Medium':
        # about 45-50% of cells
        return int(total_cells * 0.47)
    elif difficulty == 'Hard':
        # about 55-60% of cells
        return int(total_cells * 0.57)
    else:
        return int(total_cells * 0.37)  # will default to Easy


def is_valid_puzzle(board):
    """
    Check if a puzzle is valid (has a unique solution).
    """
    size = len(board)
    csp = SudokuCSP(size, board)
    
    solution_count = 0
    gen = csp.backtrack_generator()
    
    for event in gen:
        if event[0] == 'solution':
            solution_count += 1
            if solution_count > 1:
                return False  # Multiple solutions
    
    return solution_count == 1  # one solution