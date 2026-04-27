import unittest
import sys

from core.csp import SudokuCSP
from core.algorithms import (
    arc_consistency_3, 
    solve_with_ac3, 
    count_solutions, 
    get_hint,
    are_neighbors
)
from puzzles.presets import EASY_PUZZLE, MEDIUM_PUZZLE, HARD_PUZZLE, get_puzzle
from puzzles.generator import generate_puzzle, is_valid_puzzle
from gui.visualization import export_to_ascii, print_board, create_metrics_text


class TestIntegration(unittest.TestCase):
    """Integration tests for complete solver workflow"""
    
    def test_complete_solve_easy(self):
        """Test solving easy puzzle end-to-end"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        solution = None
        assignment = {}
        
        for event in csp.backtrack_generator():
            event_type = event[0]
            
            if event_type == 'assign':
                _, var, val, assign = event
                assignment = dict(assign)
                
            elif event_type == 'solution':
                _, solution = event
                break
        
        # Verify solution
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), len(csp.variables))
        
        # Verify statistics
        self.assertGreater(csp.nodes, 0)
        self.assertEqual(csp.solutions, 1)
        
        print(f"Easy puzzle solved: {csp.nodes} nodes, {csp.backtracks} backtracks")
    
    def test_complete_solve_medium(self):
        """Test solving medium puzzle end-to-end"""
        csp = SudokuCSP(9, MEDIUM_PUZZLE)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution)
        print(f"Medium puzzle solved: {csp.nodes} nodes, {csp.backtracks} backtracks")
    
    def test_complete_solve_hard(self):
        """Test solving hard puzzle end-to-end"""
        csp = SudokuCSP(9, HARD_PUZZLE)
        
        solution = None
        max_iterations = 100000  # Hard puzzles need more iterations
        
        for i, event in enumerate(csp.backtrack_generator()):
            if i > max_iterations:
                break
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution, "Hard puzzle should be solvable within iteration limit")
        print(f"Hard puzzle solved: {csp.nodes} nodes, {csp.backtracks} backtracks")
    
    def test_all_event_types(self):
        """Test that all event types are yielded correctly"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        event_types = set()
        event_data = {}
        
        for event in csp.backtrack_generator():
            event_type = event[0]
            event_types.add(event_type)
            
            # Store sample of each event type
            if event_type not in event_data:
                event_data[event_type] = event
            
            if event_type == 'solution':
                break
        
        # Verify expected event types
        self.assertIn('mrv', event_types)
        self.assertIn('lcv', event_types)
        self.assertIn('assign', event_types)
        self.assertIn('fc_ok', event_types)
        self.assertIn('solution', event_types)
        
        # Verify event structure
        mrv_event = event_data['mrv']
        self.assertEqual(len(mrv_event), 3)  # (type, var, domain)
        self.assertIsInstance(mrv_event[1], tuple)  # var is (row, col)
        self.assertIsInstance(mrv_event[2], list)   # domain is list
        
        assign_event = event_data['assign']
        self.assertEqual(len(assign_event), 4)  # (type, var, val, assignment)
        
        print(f"Event types seen: {event_types}")
    
    def test_forward_checking_failure(self):
        """Test that forward checking detects failures"""
        # Create a puzzle that will force some backtracks
        csp = SudokuCSP(9, MEDIUM_PUZZLE)
        
        fc_fails = 0
        unassigns = 0
        
        for event in csp.backtrack_generator():
            if event[0] == 'fc_fail':
                fc_fails += 1
            elif event[0] == 'unassign':
                unassigns += 1
            elif event[0] == 'solution':
                break
        
        # Medium puzzles typically need some backtracking
        print(f"FC failures: {fc_fails}, Unassigns: {unassigns}")
    
    def test_solution_validity(self):
        """Test that solution is actually valid"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        # Build complete board
        board = [row[:] for row in EASY_PUZZLE]
        for (r, c), val in solution.items():
            board[r][c] = val
        
        # Check all rows
        for row in board:
            self.assertEqual(len(set(row)), 9, "Row should have unique values 1-9")
        
        # Check all columns
        for c in range(9):
            col = [board[r][c] for r in range(9)]
            self.assertEqual(len(set(col)), 9, "Column should have unique values 1-9")
        
        # Check all 3x3 boxes
        for box_r in range(3):
            for box_c in range(3):
                box = []
                for r in range(3):
                    for c in range(3):
                        box.append(board[box_r * 3 + r][box_c * 3 + c])
                self.assertEqual(len(set(box)), 9, "Box should have unique values 1-9")
        
        print("Solution is valid!")


class TestAlgorithms(unittest.TestCase):
    """Test additional algorithms"""
    
    def test_are_neighbors(self):
        """Test neighbor detection"""
        # Same row
        self.assertTrue(are_neighbors((0, 0), (0, 5), 3))
        self.assertTrue(are_neighbors((0, 0), (0, 8), 3))
        
        # Same column
        self.assertTrue(are_neighbors((0, 0), (5, 0), 3))
        self.assertTrue(are_neighbors((0, 0), (8, 0), 3))
        
        # Same box
        self.assertTrue(are_neighbors((0, 0), (2, 2), 3))
        self.assertTrue(are_neighbors((3, 3), (5, 5), 3))
        
        # Not neighbors
        self.assertFalse(are_neighbors((0, 0), (3, 3), 3))
        self.assertFalse(are_neighbors((0, 0), (5, 5), 3))
    
    def test_solve_with_ac3(self):
        """Test AC-3 enhanced solving"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        solution = solve_with_ac3(csp)
        
        self.assertIsNotNone(solution)
        self.assertEqual(len(solution), len(csp.variables))
        print("AC-3 enhanced solve completed")
    
    def test_count_solutions(self):
        """Test solution counting"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        count = count_solutions(csp, max_count=2)
        
        self.assertEqual(count, 1, "Easy puzzle should have exactly 1 solution")
    
    def test_get_hint(self):
        """Test hint generation"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        hint = get_hint(csp, {})
        
        self.assertIsNotNone(hint)
        var, value = hint
        self.assertIn(var, csp.variables)
        self.assertIn(value, csp.initial_domains[var])
        
        print(f"Hint: Fill {var} with {value}")


class TestVisualization(unittest.TestCase):
    """Test visualization utilities"""
    
    def test_export_to_ascii(self):
        """Test ASCII export"""
        ascii_art = export_to_ascii(EASY_PUZZLE)
        
        self.assertIsInstance(ascii_art, str)
        self.assertIn('│', ascii_art)
        self.assertIn('─', ascii_art)
        self.assertIn('5', ascii_art)  # Known value in easy puzzle
        self.assertIn('·', ascii_art)  # Empty cell marker
        
        print("\nASCII export:")
        print(ascii_art)
    
    def test_create_metrics_text(self):
        """Test metrics text generation"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        csp.nodes = 50
        csp.backtracks = 5
        csp.solutions = 0
        
        metrics = create_metrics_text(csp, {}, "Testing")
        
        self.assertIn("Sudoku 9x9", metrics)
        self.assertIn("Nodes visited: 50", metrics)
        self.assertIn("Backtracks: 5", metrics)
        self.assertIn("Status: Testing", metrics)
        
        print("\nMetrics text:")
        print(metrics)


class TestPuzzleGeneration(unittest.TestCase):
    """Test puzzle generation"""
    
    def test_generate_and_solve_easy(self):
        """Test generating and solving easy puzzle"""
        puzzle = generate_puzzle(9, 'Easy')
        csp = SudokuCSP(9, puzzle)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution)
        print(f"Generated easy puzzle solved: {csp.nodes} nodes")
    
    def test_generate_and_solve_medium(self):
        """Test generating and solving medium puzzle"""
        puzzle = generate_puzzle(9, 'Medium')
        csp = SudokuCSP(9, puzzle)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution)
        print(f"Generated medium puzzle solved: {csp.nodes} nodes")
    
    def test_generate_and_solve_hard(self):
        """Test generating and solving hard puzzle"""
        puzzle = generate_puzzle(9, 'Hard')
        csp = SudokuCSP(9, puzzle)
        
        solution = None
        max_iterations = 100000
        
        for i, event in enumerate(csp.backtrack_generator()):
            if i > max_iterations:
                break
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution)
        print(f"Generated hard puzzle solved: {csp.nodes} nodes")
    
    def test_get_puzzle_returns_copy(self):
        """Test that get_puzzle returns a copy, not original"""
        puzzle1 = get_puzzle('Easy', 0)
        puzzle2 = get_puzzle('Easy', 0)
        
        # Modify puzzle1
        puzzle1[0][0] = 999
        
        # puzzle2 should be unchanged
        self.assertNotEqual(puzzle2[0][0], 999)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_invalid_size(self):
        """Test that invalid size raises error"""
        with self.assertRaises(ValueError):
            SudokuCSP(size=5)  # Not a perfect square
    
    def test_almost_complete_puzzle(self):
        """Test puzzle with only one empty cell"""
        almost_complete = [
            [5, 3, 4, 6, 7, 8, 9, 1, 2],
            [6, 7, 2, 1, 9, 5, 3, 4, 8],
            [1, 9, 8, 3, 4, 2, 5, 6, 7],
            [8, 5, 9, 7, 6, 1, 4, 2, 3],
            [4, 2, 6, 8, 5, 3, 7, 9, 1],
            [7, 1, 3, 9, 2, 4, 8, 5, 6],
            [9, 6, 1, 5, 3, 7, 2, 8, 4],
            [2, 8, 7, 4, 1, 9, 6, 3, 5],
            [3, 4, 5, 2, 8, 6, 1, 7, 0]  # Last cell empty
        ]
        
        csp = SudokuCSP(9, almost_complete)
        self.assertEqual(len(csp.variables), 1)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        self.assertIsNotNone(solution)
        self.assertEqual(solution[(8, 8)], 9)
    
    def test_empty_board(self):
        """Test empty board has many solutions"""
        empty_board = [[0] * 9 for _ in range(9)]
        
        csp = SudokuCSP(9, empty_board)
        count = count_solutions(csp, max_count=2)
        
        self.assertEqual(count, 2)  # Multiple solutions exist
    
    def test_reset_statistics(self):
        """Test that reset clears statistics"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        # Do some solving
        for i, event in enumerate(csp.backtrack_generator()):
            if i > 10:
                break
        
        self.assertGreater(csp.nodes, 0)
        
        # Reset
        csp.reset()
        
        self.assertEqual(csp.nodes, 0)
        self.assertEqual(csp.backtracks, 0)
        self.assertEqual(csp.solutions, 0)


def run_all_tests():
    """Run all integration tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAlgorithms))
    suite.addTests(loader.loadTestsFromTestCase(TestVisualization))
    suite.addTests(loader.loadTestsFromTestCase(TestPuzzleGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
