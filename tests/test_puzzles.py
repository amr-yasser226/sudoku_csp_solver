import unittest

from puzzles.presets import (
    EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE,
    PUZZLES, get_puzzle
)
from puzzles.generator import generate_puzzle, is_valid_puzzle
from core.csp import SudokuCSP


class TestPresetPuzzles(unittest.TestCase):
    
    def test_puzzle_dimensions(self):
        """Test that all preset puzzles are 9x9"""
        self.assertEqual(len(EASY_PUZZLE), 9)
        self.assertEqual(len(MEDIUM_PUZZLE), 9)
        self.assertEqual(len(HARD_PUZZLE), 9)
        
        for row in EASY_PUZZLE:
            self.assertEqual(len(row), 9)
        
        for row in MEDIUM_PUZZLE:
            self.assertEqual(len(row), 9)
        
        for row in HARD_PUZZLE:
            self.assertEqual(len(row), 9)
    
    def test_puzzle_values(self):
        """Test that puzzles contain only valid values (0-9)"""
        for puzzle in [EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE]:
            for row in puzzle:
                for val in row:
                    self.assertGreaterEqual(val, 0)
                    self.assertLessEqual(val, 9)
    
    def test_puzzle_has_empty_cells(self):
        """Test that puzzles have empty cells"""
        for puzzle in [EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE]:
            empty_count = sum(row.count(0) for row in puzzle)
            self.assertGreater(empty_count, 0, "Puzzle should have empty cells")
    
    def test_puzzle_solvability(self):
        """Test that preset puzzles are solvable"""
        for puzzle_name, puzzle in [
            ('Easy', EASY_PUZZLE),
            ('Medium', MEDIUM_PUZZLE)
        ]:
            with self.subTest(puzzle=puzzle_name):
                csp = SudokuCSP(9, puzzle)
                
                solution = None
                max_iterations = 100000  # Prevent infinite loops
                iteration = 0
                
                for event in csp.backtrack_generator():
                    iteration += 1
                    if iteration > max_iterations:
                        break
                    if event[0] == 'solution':
                        solution = event[1]
                        break
                
                self.assertIsNotNone(solution, f"{puzzle_name} puzzle should be solvable")
    
    def test_get_puzzle(self):
        """Test get_puzzle function"""
        # Test getting Easy puzzle
        puzzle = get_puzzle('Easy', 0)
        self.assertEqual(len(puzzle), 9)
        
        # Test getting Medium puzzle
        puzzle = get_puzzle('Medium', 0)
        self.assertEqual(len(puzzle), 9)
        
        # Test default behavior with invalid difficulty
        puzzle = get_puzzle('Invalid', 0)
        self.assertEqual(len(puzzle), 9)
        
        # Test index bounds
        puzzle = get_puzzle('Easy', 999)  # Should wrap to 0
        self.assertEqual(len(puzzle), 9)
    
    def test_puzzles_dictionary(self):
        """Test PUZZLES dictionary structure"""
        self.assertIn('Easy', PUZZLES)
        self.assertIn('Medium', PUZZLES)
        self.assertIn('Hard', PUZZLES)
        
        # Each difficulty should have a list of puzzles
        for difficulty, puzzle_list in PUZZLES.items():
            self.assertIsInstance(puzzle_list, list)
            self.assertGreater(len(puzzle_list), 0)


class TestPuzzleGenerator(unittest.TestCase):
    """Test puzzle generation"""
    
    def test_generate_easy_puzzle(self):
        """Test generating an easy puzzle"""
        puzzle = generate_puzzle(size=9, difficulty='Easy')
        
        # Check dimensions
        self.assertEqual(len(puzzle), 9)
        for row in puzzle:
            self.assertEqual(len(row), 9)
        
        # Check values
        for row in puzzle:
            for val in row:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 9)
        
        # Check has empty cells
        empty_count = sum(row.count(0) for row in puzzle)
        self.assertGreater(empty_count, 0)
    
    def test_generate_medium_puzzle(self):
        """Test generating a medium puzzle"""
        puzzle = generate_puzzle(size=9, difficulty='Medium')
        
        # Medium should have more empty cells than Easy
        empty_count = sum(row.count(0) for row in puzzle)
        self.assertGreater(empty_count, 30)
    
    def test_generate_hard_puzzle(self):
        """Test generating a hard puzzle"""
        puzzle = generate_puzzle(size=9, difficulty='Hard')
        
        # Hard should have most empty cells
        empty_count = sum(row.count(0) for row in puzzle)
        self.assertGreater(empty_count, 40)
    
    def test_generated_puzzle_difficulty_ordering(self):
        """Test that difficulty levels have expected empty cell counts"""
        easy = generate_puzzle(size=9, difficulty='Easy')
        medium = generate_puzzle(size=9, difficulty='Medium')
        hard = generate_puzzle(size=9, difficulty='Hard')
        
        easy_empty = sum(row.count(0) for row in easy)
        medium_empty = sum(row.count(0) for row in medium)
        hard_empty = sum(row.count(0) for row in hard)
        
        # Generally: easy < medium < hard (though randomness can vary)
        self.assertLess(easy_empty, hard_empty)
    
    def test_generated_puzzle_has_clues(self):
        """Test that generated puzzles have given clues"""
        puzzle = generate_puzzle(size=9, difficulty='Easy')
        
        given_count = sum(1 for row in puzzle for val in row if val != 0)
        self.assertGreater(given_count, 0, "Puzzle should have initial clues")
    
    def test_is_valid_puzzle_with_easy(self):
        """Test puzzle validation with easy puzzle"""
        # EASY_PUZZLE should be valid (unique solution)
        # Note: This test might be slow
        result = is_valid_puzzle(EASY_PUZZLE)
        self.assertTrue(result, "Easy puzzle should be valid")
    
    def test_is_valid_puzzle_with_multiple_solutions(self):
        """Test validation catches puzzles with multiple solutions"""
        # Nearly empty board will have multiple solutions
        mostly_empty = [[0 for _ in range(9)] for _ in range(9)]
        mostly_empty[0][0] = 1  # Just one clue
        
        # Use small iteration limit since we just need to find 2 solutions
        result = is_valid_puzzle(mostly_empty, max_iterations=5000)
        self.assertFalse(result, "Puzzle with multiple solutions should be invalid")
    
    def test_is_valid_puzzle_with_no_solution(self):
        """Test validation catches unsolvable puzzles"""
        # Create invalid puzzle (two 1's in same row)
        invalid = [[0 for _ in range(9)] for _ in range(9)]
        invalid[0][0] = 1
        invalid[0][1] = 1  # Conflict!
        
        # The quick domain check should catch this immediately
        result = is_valid_puzzle(invalid, max_iterations=1000)
        self.assertFalse(result, "Unsolvable puzzle should be invalid")


class TestPuzzleProperties(unittest.TestCase):
    """Test mathematical properties of puzzles"""
    
    def test_no_duplicate_clues_in_row(self):
        """Test that initial clues don't violate row constraint"""
        for puzzle in [EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE]:
            for row in puzzle:
                # Get non-zero values
                clues = [val for val in row if val != 0]
                # Check no duplicates
                self.assertEqual(len(clues), len(set(clues)), 
                               "Row should not have duplicate clues")
    
    def test_no_duplicate_clues_in_column(self):
        """Test that initial clues don't violate column constraint"""
        for puzzle in [EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE]:
            for col in range(9):
                clues = [puzzle[row][col] for row in range(9) if puzzle[row][col] != 0]
                self.assertEqual(len(clues), len(set(clues)),
                               "Column should not have duplicate clues")
    
    def test_no_duplicate_clues_in_box(self):
        """Test that initial clues don't violate box constraint"""
        for puzzle in [EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE]:
            for box_row in range(3):
                for box_col in range(3):
                    clues = []
                    for r in range(3):
                        for c in range(3):
                            val = puzzle[box_row * 3 + r][box_col * 3 + c]
                            if val != 0:
                                clues.append(val)
                    
                    self.assertEqual(len(clues), len(set(clues)),
                                   f"Box ({box_row},{box_col}) should not have duplicate clues")
    
    def test_puzzle_symmetry_property(self):
        """Test if puzzles have any symmetry (informational test)"""
        # This is just to analyze puzzle properties, not a pass/fail test
        for puzzle_name, puzzle in [('Easy', EASY_PUZZLE)]:
            # Check rotational symmetry
            symmetric = True
            for r in range(9):
                for c in range(9):
                    if (puzzle[r][c] == 0) != (puzzle[8-r][8-c] == 0):
                        symmetric = False
                        break
            
            # Just print info, don't assert
            print(f"\n{puzzle_name} puzzle has rotational symmetry: {symmetric}")


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()