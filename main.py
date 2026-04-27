import sys
import matplotlib.pyplot as plt
from gui.dashboard import SudokuDashboard
from puzzles.presets import EASY_PUZZLE


def main() -> None:
    try:
        print("=" * 50)
        print("Sudoku CSP Solver")
        print("Using: MRV + LCV + Forward Checking")
        print("=" * 50)
        
        # Create and run the dashboard
        dash = SudokuDashboard(size=9, initial_board=EASY_PUZZLE, speed=0.05)
        plt.show()
        
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()