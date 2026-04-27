import unittest

from core.csp import SudokuCSP
from puzzles.presets import EASY_PUZZLE, MEDIUM_PUZZLE


class TestSudokuCSP(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.easy_csp = SudokuCSP(9, EASY_PUZZLE)
        self.medium_csp = SudokuCSP(9, MEDIUM_PUZZLE)
    
    def test_initialization(self):
        """Test CSP initialization"""
        self.assertEqual(self.easy_csp.size, 9)
        self.assertEqual(self.easy_csp.box_size, 3)
        self.assertIsInstance(self.easy_csp.variables, list)
        self.assertIsInstance(self.easy_csp.initial_domains, dict)
    
    def test_variables_setup(self):
        """Test that variables are correctly identified"""
        # Count empty cells in EASY_PUZZLE
        empty_count = sum(row.count(0) for row in EASY_PUZZLE)
        self.assertEqual(len(self.easy_csp.variables), empty_count)
        
        # All variables should be tuples
        for var in self.easy_csp.variables:
            self.assertIsInstance(var, tuple)
            self.assertEqual(len(var), 2)
    
    def test_initial_domains(self):
        """Test initial domain setup"""
        for var in self.easy_csp.variables:
            self.assertIn(var, self.easy_csp.initial_domains)
            domain = self.easy_csp.initial_domains[var]
            self.assertIsInstance(domain, list)
            # Domain should be subset of 1-9
            self.assertTrue(all(1 <= v <= 9 for v in domain))
    
    def test_is_consistent_row(self):
        """Test row constraint checking"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        assignment = {(0, 2): 4}  # Assign 4 to row 0, col 2
        
        # Should fail - 4 is already at (4, 0) which is same value conflict
        # Let's test with a clear case
        assignment = {}
        # Assign different values in same row
        assignment[(0, 0)] = 1
        
        # Try to assign same value in same row - should be inconsistent
        self.assertFalse(csp.is_consistent((0, 1), 1, assignment))
        
        # Try to assign different value - should be consistent
        self.assertTrue(csp.is_consistent((0, 1), 2, assignment))
    
    def test_is_consistent_column(self):
        """Test column constraint checking"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        assignment = {(0, 0): 1}
        
        # Same column, same value - inconsistent
        self.assertFalse(csp.is_consistent((1, 0), 1, assignment))
        
        # Same column, different value - consistent
        self.assertTrue(csp.is_consistent((1, 0), 2, assignment))
    
    def test_is_consistent_box(self):
        """Test box constraint checking"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        assignment = {(0, 0): 1}
        
        # Same box (top-left 3x3), same value - inconsistent
        self.assertFalse(csp.is_consistent((1, 1), 1, assignment))
        
        # Same box, different value - consistent
        self.assertTrue(csp.is_consistent((1, 1), 2, assignment))
    
    def test_forward_check(self):
        """Test forward checking"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        domains = {v: list(csp.initial_domains[v]) for v in csp.variables}
        
        # Pick a variable and value
        var = csp.variables[0]
        value = domains[var][0] if domains[var] else 1
        
        new_domains, removed = csp.forward_check(var, value, domains)
        
        # Forward check should not fail for valid puzzles initially
        self.assertIsNotNone(new_domains)
        self.assertIsInstance(removed, dict)
    
    def test_mrv_heuristic(self):
        """Test MRV (Minimum Remaining Values) heuristic"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        domains = {v: list(csp.initial_domains[v]) for v in csp.variables}
        assignment = {}
        
        var = csp.select_unassigned_var(domains, assignment)
        
        # Selected variable should have smallest domain
        self.assertIn(var, csp.variables)
        selected_domain_size = len(domains[var])
        
        # Check it's actually minimum (or tied for minimum)
        for v in csp.variables:
            if v not in assignment:
                self.assertLessEqual(selected_domain_size, len(domains[v]))
                # If we break ties by index, our selection should be <= in size
    
    def test_lcv_heuristic(self):
        """Test LCV (Least Constraining Value) heuristic"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        domains = {v: list(csp.initial_domains[v]) for v in csp.variables}
        assignment = {}
        
        var = csp.variables[0]
        ordered_values = csp.order_domain_values(var, domains, assignment)
        
        # Should return a list
        self.assertIsInstance(ordered_values, list)
        
        # Should contain same values as domain (just reordered)
        self.assertEqual(set(ordered_values), set(domains[var]))
    
    def test_solve_easy_puzzle(self):
        """Test solving an easy puzzle"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        solution = None
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                solution = event[1]
                break
        
        # Should find a solution
        self.assertIsNotNone(solution)
        
        # Solution should assign all variables
        self.assertEqual(len(solution), len(csp.variables))
        
        # All values should be 1-9
        for val in solution.values():
            self.assertGreaterEqual(val, 1)
            self.assertLessEqual(val, 9)
    
    def test_backtrack_generator_events(self):
        """Test that backtrack generator yields expected events"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        event_types = set()
        count = 0
        max_events = 100  # Just check first 100 events
        
        for event in csp.backtrack_generator():
            event_types.add(event[0])
            count += 1
            if count >= max_events:
                break
        
        # Should see various event types
        self.assertIn('mrv', event_types)
        self.assertIn('lcv', event_types)
        self.assertIn('assign', event_types)
    
    def test_statistics_tracking(self):
        """Test that solver tracks statistics correctly"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        # Initially should be zero
        self.assertEqual(csp.nodes, 0)
        self.assertEqual(csp.backtracks, 0)
        self.assertEqual(csp.solutions, 0)
        
        # Run solver
        for event in csp.backtrack_generator():
            if event[0] == 'solution':
                break
        
        # Statistics should be updated
        self.assertGreater(csp.nodes, 0)
        self.assertEqual(csp.solutions, 1)
    
    def test_empty_board(self):
        """Test with completely empty board"""
        empty_board = [[0 for _ in range(9)] for _ in range(9)]
        csp = SudokuCSP(9, empty_board)
        
        # Should have 81 variables
        self.assertEqual(len(csp.variables), 81)
        
        # Each variable should have full domain 1-9
        for var in csp.variables:
            self.assertEqual(len(csp.initial_domains[var]), 9)
    
    def test_almost_complete_board(self):
        """Test with almost complete board (one empty cell)"""
        # Create a valid completed board first
        complete_board = [
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
        
        csp = SudokuCSP(9, complete_board)
        
        # Should have 1 variable
        self.assertEqual(len(csp.variables), 1)
        
        # Should have only one value in domain
        var = csp.variables[0]
        self.assertEqual(len(csp.initial_domains[var]), 1)


class TestConstraints(unittest.TestCase):
    """Test constraint checking"""
    
    def test_count_constraints(self):
        """Test constraint counting for degree heuristic"""
        csp = SudokuCSP(9, EASY_PUZZLE)
        
        var = csp.variables[0]
        assignment = {}
        
        count = csp._count_constraints(var, assignment)
        
        # Should have constraints (row + column + box neighbors)
        self.assertGreater(count, 0)
        # Maximum would be 20 (8 in row + 8 in column + 4 in box, without duplicates)
        self.assertLessEqual(count, 20)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    run_tests()