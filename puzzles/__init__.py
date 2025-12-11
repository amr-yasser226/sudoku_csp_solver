"""
Puzzle data and generation module
"""
from .presets import EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE, PUZZLES, get_puzzle
from .generator import generate_puzzle, is_valid_puzzle

__all__ = [
    'EASY_PUZZLE',
    'MEDIUM_PUZZLE', 
    'HARD_PUZZLE',
    'PUZZLES',
    'get_puzzle',
    'generate_puzzle',
    'is_valid_puzzle'
]