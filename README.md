# Sudoku CSP Solver

## Overview

An advanced, interactive Sudoku solver implemented using Constraint Satisfaction Problem (CSP) paradigms. The core engine features real-time visual tracing, optimized backtracking, and constraint propagation mechanisms to guarantee sound and complete puzzle resolutions. This project demonstrates high-performance search techniques paired with real-time heuristic visualizations.

## Architecture and Core Algorithms

The solver operates on sophisticated CSP principles to ensure maximum computational efficiency and minimal backtracking states:

- **Minimum Remaining Values (MRV)**: A fail-first variable ordering heuristic that selects the cell with the fewest valid candidates, prioritizing tightly constrained variables to prune the search tree early.
- **Least Constraining Value (LCV)**: A value ordering strategy that evaluates domains dynamically and prioritizes assignments that leave the maximal number of options for adjacent unassigned variables.
- **Forward Checking**: A look-ahead constraint propagation mechanism that dynamically prunes impossible domain values from unassigned variables after each node assignment, detecting failure points instantaneously.
- **Arc Consistency 3 (AC-3)**: Implemented as an optional pre-processing and constraint propagation layer to maintain arc consistency across the constraint network, further reducing the domain state space prior to initiating standard backtracking.

## Key Features

- **Real-time Visualization Dashboard**: Utilizing Matplotlib to visualize algorithm execution step-by-step, highlighting variable assignments, constraint propagation phases, and domain reductions.
- **Asynchronous Execution Engines**: Leverages Python generator expressions to provide non-blocking sequential event tracking for stable UI rendering and state observation.
- **Strict Typing and Integrity**: Enforces comprehensive PEP 484 static typing throughout the structural codebase, promoting robust API design and predictability.
- **Robust Puzzle Generation**: Employs a backtracking algorithmic generator capable of deterministic puzzle generation across defined difficulty schemas. Includes rigorous validation checks to guarantee all generated puzzles possess a singular unique solution.
- **Performance Profiling**: Tracks and displays visited nodes, recursion depth, domain sizes, and backtracking events continuously to empirically evaluate heuristic efficacy.

## Technical Requirements

- Python 3.10+
- NumPy
- Matplotlib (Qt5Agg backend recommended for optimal UI rendering performance)
- Pytest (for executing test suites)

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/amr-yasser226/sudoku_csp_solver.git
cd sudoku_csp_solver
```

2. Establish an isolated virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
# On Windows environments: venv\Scripts\activate
```

3. Install the requisite dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

Execute the main controller script to launch the interactive dashboard:

```bash
python main.py
```

### Dashboard Controls

| Control | Function |
|---------|----------|
| **Step** | Execute and visualize a single discrete algorithmic step. |
| **Run** | Continuously execute the solver while rendering state transitions. |
| **Pause** | Interrupt and inspect the running solver state. |
| **Reset** | Restore the solver and board to their initial configurations. |
| **Solve All** | Bypass step visualization to compute the solution at maximum efficiency. |
| **New Puzzle** | Instantiate a freshly generated and validated Sudoku board. |
| **Speed Slider** | Modulate the transition speed of the visualization sequence. |

### API and Integration

The underlying computational elements can be integrated independently of the graphical interface.

```python
from core.csp import SudokuCSP
from puzzles.presets import EASY_PUZZLE

# Initialize the constraint satisfaction problem
csp = SudokuCSP(size=9, initial_board=EASY_PUZZLE)

# Iterate through solving states
for event in csp.backtrack_generator():
    if event[0] == 'solution':
        solution = event[1]
        print(f"Optimal solution located. Nodes Visited: {csp.nodes}, Backtracks: {csp.backtracks}")
        break
```

## Testing

The project maintains a rigorous testing environment covering integration logic, constraint verifications, heuristics behavior, and generator validations.

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Execute standard suite
python -m pytest tests/ -v

# Execute suite with coverage tracking
python -m pytest tests/ -v --cov=core --cov=puzzles
```

## Project Layout

```text
sudoku_csp_solver/
├── main.py              # Application entry and UI controller
├── core/
│   ├── csp.py           # Core CSP solver engine (MRV, LCV, Forward Checking)
│   └── algorithms.py    # Supplementary constraint processing (AC-3)
├── gui/
│   ├── dashboard.py     # Matplotlib interactive graphical dashboard
│   └── visualization.py # Render parameters and utilities
├── puzzles/
│   ├── generator.py     # Deterministic board generator and uniqueness validator
│   └── presets.py       # Statically defined testing configurations
├── tests/
│   ├── test_csp.py      # Automated tests for core resolution logic
│   ├── test_integration.py # Automated tests for end-to-end functionality
│   └── test_puzzles.py  # Automated tests for board consistency
└── requirements.txt     # Dependency definitions
```

## Performance Profile

Computational footprint on standard 9x9 constraints:
- **Easy Complexity**: ~50-100 visited nodes
- **Medium Complexity**: ~100-500 visited nodes
- **Hard Complexity**: ~500-5000 visited nodes

The synergistic execution of MRV, LCV, and Forward Checking yields substantial performance improvements over naive recursive backtracking solutions.

## License

This project is licensed under the MIT License. Reference the LICENSE file for explicit terms.

## Author

Amr Yasser
Course: CSAI 301 - Artificial Intelligence

## Acknowledgments

Theoretical foundations derived from "Artificial Intelligence: A Modern Approach" (Russell & Norvig).