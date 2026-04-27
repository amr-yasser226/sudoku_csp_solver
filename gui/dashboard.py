from __future__ import annotations
from typing import Any

import matplotlib
# Try Qt5Agg backend, fall back to default if not available
try:
    matplotlib.use('Qt5Agg')
except Exception:
    pass  # Use default backend

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.widgets import Button, Slider
from matplotlib.animation import FuncAnimation
import numpy as np

from core.csp import SudokuCSP
from puzzles.generator import generate_puzzle

# Constants
EVENTS_PER_FRAME = 100
DEFAULT_SPEED = 0.05
MIN_SPEED = 0.01
MAX_SPEED = 0.5

# Colors
CELL_COLOR = '#ffffff'
GRID_LIGHT = '#cccccc'
GRID_DARK = 'black'
INITIAL_NUMBER_COLOR = 'black'
SOLVED_NUMBER_COLOR = 'blue'
HIGHLIGHT_TRY_COLOR = 'red'
HIGHLIGHT_SUCCESS_COLOR = 'green'
BUTTON_ACTIVE_COLOR = '#ffcccc'
BUTTON_DEFAULT_COLOR = '#eeeeee'


class SudokuDashboard:
    
    def __init__(
        self, 
        size: int = 9, 
        initial_board: list[list[int]] | None = None, 
        speed: float = DEFAULT_SPEED
    ) -> None:
        if size <= 0:
            raise ValueError("Size must be positive")
        
        box_size = int(np.sqrt(size))
        if box_size * box_size != size:
            raise ValueError(f"Size must be a perfect square, got {size}")
        
        self.size = size
        self.box_size = box_size
        self.speed = speed
        self.initial_board = initial_board
        self.csp = SudokuCSP(size, initial_board)
        self.gen: Any = None
        self.running = False
        self.solve_all_mode = False
        self.assignment: dict[tuple[int, int], int] = {}
        self.domains: dict[tuple[int, int], list[int]] = {
            v: list(self.csp.initial_domains[v]) for v in self.csp.variables
        }
        self.highlight: tuple[int, int, str] | None = None
        self.animation: FuncAnimation | None = None
        self._build_ui()
        self.reset()
    
    def _build_ui(self) -> None:
        """Build the user interface with board and controls."""
        plt.close('all')
        self.fig = plt.figure(figsize=(14, 9))
        self.fig.canvas.manager.set_window_title('Sudoku CSP Solver')
        
        # Board area
        self.ax_board = self.fig.add_axes([0.05, 0.15, 0.50, 0.75])
        self.ax_board.axis('off')
        self.ax_board.set_aspect('equal')
        
        # Control buttons
        ax_step = self.fig.add_axes([0.60, 0.82, 0.10, 0.05])
        ax_run = self.fig.add_axes([0.71, 0.82, 0.10, 0.05])
        ax_reset = self.fig.add_axes([0.82, 0.82, 0.10, 0.05])
        ax_solve = self.fig.add_axes([0.60, 0.75, 0.10, 0.05])
        ax_new = self.fig.add_axes([0.71, 0.75, 0.10, 0.05])
        
        self.btn_step = Button(ax_step, 'Step')
        self.btn_run = Button(ax_run, 'Run')
        self.btn_reset = Button(ax_reset, 'Reset')
        self.btn_solve = Button(ax_solve, 'Solve All')
        self.btn_new = Button(ax_new, 'New Puzzle')
        
        self.btn_step.on_clicked(self.on_step)
        self.btn_run.on_clicked(self.on_run)
        self.btn_reset.on_clicked(self.on_reset)
        self.btn_solve.on_clicked(self.on_solve_all)
        self.btn_new.on_clicked(self.on_new_puzzle)
        
        # Speed slider
        ax_speed = self.fig.add_axes([0.60, 0.67, 0.32, 0.03])
        self.slider_speed = Slider(ax_speed, 'Speed', MIN_SPEED, MAX_SPEED, valinit=self.speed)
        self.slider_speed.on_changed(self.on_speed)
        
        # Metrics panel
        self.ax_metrics = self.fig.add_axes([0.60, 0.15, 0.35, 0.48])
        self.ax_metrics.axis('off')
        self.metrics_text = self.ax_metrics.text(0, 1, '', va='top', family='monospace', fontsize=10)
        
        self.draw_board()
        plt.show(block=False)
    
    def reset(self) -> None:
        """Reset the solver to initial state."""
        # Stop any running animation first
        if self.animation:
            self.animation.event_source.stop()
            self.animation = None
        
        self.csp = SudokuCSP(self.size, self.initial_board)
        self.csp.reset()
        self.gen = None
        self.running = False
        self.solve_all_mode = False
        self.assignment = {}
        self.domains = {v: list(self.csp.initial_domains[v]) for v in self.csp.variables}
        self.highlight = None
        self.update_metrics()
        self.draw_board()
        
        # Reset button states
        try:
            self.btn_solve.ax.set_facecolor(BUTTON_DEFAULT_COLOR)
            self.btn_run.label.set_text("Run")
            self.btn_solve.label.set_text("Solve All")
        except AttributeError:
            pass
    
    def draw_board(self) -> None:
        """Draw the Sudoku board with current state."""
        N = self.size
        box = self.box_size
        self.ax_board.clear()
        self.ax_board.set_xlim(0, N)
        self.ax_board.set_ylim(0, N)
        self.ax_board.set_xticks([])
        self.ax_board.set_yticks([])
        
        # Draw grid cells
        for r in range(N):
            for c in range(N):
                self.ax_board.add_patch(patches.Rectangle(
                    (c, N - r - 1), 1, 1, 
                    facecolor=CELL_COLOR, 
                    edgecolor=GRID_LIGHT, 
                    linewidth=0.5
                ))
        
        # Draw thick box borders
        for i in range(0, N + 1, box):
            self.ax_board.axhline(i, color=GRID_DARK, linewidth=2)
            self.ax_board.axvline(i, color=GRID_DARK, linewidth=2)
        
        # Draw initial numbers (given clues) in black
        for r in range(N):
            for c in range(N):
                if self.csp.initial_board[r][c] != 0:
                    val = self.csp.initial_board[r][c]
                    self.ax_board.text(
                        c + 0.5, N - r - 1 + 0.5, str(val), 
                        fontsize=20, ha='center', va='center',
                        color=INITIAL_NUMBER_COLOR, weight='bold'
                    )
        
        # Draw assigned values (from CSP solver) in blue
        for (r, c), val in self.assignment.items():
            self.ax_board.text(
                c + 0.5, N - r - 1 + 0.5, str(val), 
                fontsize=20, ha='center', va='center',
                color=SOLVED_NUMBER_COLOR, weight='normal'
            )
        
        # Highlight current cell
        if self.highlight:
            r, c, typ = self.highlight
            color = HIGHLIGHT_TRY_COLOR if typ == 'try' else HIGHLIGHT_SUCCESS_COLOR
            self.ax_board.add_patch(patches.Rectangle(
                (c, N - r - 1), 1, 1, 
                fill=False, 
                edgecolor=color, 
                linewidth=3
            ))
        
        # Show domain sizes for empty cells (only in step mode)
        if not self.solve_all_mode:
            for (r, c) in self.csp.variables:
                if (r, c) not in self.assignment:
                    ds = len(self.domains.get((r, c), []))
                    if ds > 0:
                        self.ax_board.text(
                            c + 0.1, N - r - 0.9, f'{ds}', 
                            fontsize=7, color='gray'
                        )
        
        self.fig.canvas.draw_idle()
    
    def update_metrics(self, extra: dict[str, Any] | None = None) -> None:
        """Update the metrics display panel."""
        m = self.csp
        total_vars = len(self.csp.variables)
        assigned = len(self.assignment)
        
        if self.solve_all_mode:
            status = "Solving (fast)"
        elif self.running:
            status = "Step-by-step"
        else:
            status = "Paused"
        
        txt = [
            f"Sudoku {self.size}x{self.size}",
            f"Variables: {total_vars}",
            f"Assigned: {assigned} / {total_vars}",
            "",
            f"Nodes visited: {m.nodes}",
            f"Backtracks: {m.backtracks}",
            f"Solutions found: {m.solutions}",
            "",
            f"Current variable (MRV): {extra.get('mrv') if extra else '-'}",
            f"Domain size: {extra.get('domain_size') if extra else '-'}",
            "",
            f"Status: {status}",
        ]
        
        self.metrics_text.set_text("\n".join(txt))
        self.fig.canvas.draw_idle()
    
    def handle_event(self, ev: tuple[str, ...]) -> None:
        """Handle events from the CSP solver generator."""
        typ = ev[0]
        
        if typ == 'mrv':
            _, var, domain = ev
            if not self.solve_all_mode:
                self.update_metrics(extra={'mrv': var, 'domain_size': len(domain)})
        
        elif typ == 'lcv':
            pass  # Skip for performance
        
        elif typ == 'assign':
            _, var, val, assign = ev
            self.assignment = dict(assign)
            
            # Update domains snapshot
            self.domains = {v: list(self.csp.initial_domains[v]) for v in self.csp.variables}
            for (r, c), value in self.assignment.items():
                fc, _ = self.csp.forward_check((r, c), value, self.domains)
                if fc:
                    self.domains = fc
            
            self.highlight = (var[0], var[1], 'try')
            if not self.solve_all_mode:
                self.draw_board()
                self.update_metrics()
        
        elif typ == 'unassign':
            _, var, assign = ev
            self.assignment = dict(assign)
            
            # Rebuild domains snapshot
            self.domains = {v: list(self.csp.initial_domains[v]) for v in self.csp.variables}
            for (r, c), value in self.assignment.items():
                fc, _ = self.csp.forward_check((r, c), value, self.domains)
                if fc:
                    self.domains = fc
            
            self.highlight = None
            if not self.solve_all_mode:
                self.draw_board()
                self.update_metrics()
        
        elif typ == 'solution':
            _, assign = ev
            self.assignment = dict(assign)
            self.highlight = None
            self.draw_board()
            self.update_metrics()
            self.running = False
            self.solve_all_mode = False
            self.btn_run.label.set_text("Run")
            self.btn_solve.label.set_text("Solve All")
            print(f"✓ Solution found! Nodes: {self.csp.nodes}, Backtracks: {self.csp.backtracks}")
    
    # Control handlers
    def on_step(self, event: Any) -> None:
        """Handle Step button click."""
        if self.gen is None:
            self.gen = self.csp.backtrack_generator()
        try:
            ev = next(self.gen)
            self.handle_event(ev)
        except StopIteration:
            self.update_metrics()
            print("Search exhausted - no more solutions")
    
    def on_run(self, event: Any) -> None:
        """Handle Run/Pause button click."""
        if self.running:
            # Stop current animation
            self.running = False
            self.btn_run.label.set_text("Run")
            if self.animation:
                self.animation.event_source.stop()
                self.animation = None
            return
        
        if self.gen is None:
            self.gen = self.csp.backtrack_generator()
        
        self.running = True
        self.solve_all_mode = False
        self.btn_run.label.set_text("Pause")
        
        def animate(frame: int) -> None:
            if not self.running:
                if self.animation:
                    self.animation.event_source.stop()
                return
            try:
                ev = next(self.gen)
                self.handle_event(ev)
            except StopIteration:
                self.running = False
                self.btn_run.label.set_text("Run")
                if self.animation:
                    self.animation.event_source.stop()
                    self.animation = None
        
        self.animation = FuncAnimation(
            self.fig, animate, interval=int(self.speed * 1000), 
            cache_frame_data=False, repeat=False
        )
        plt.draw()
    
    def on_reset(self, event: Any) -> None:
        """Handle Reset button click."""
        if self.animation:
            self.animation.event_source.stop()
        self.reset()
    
    def on_solve_all(self, event: Any) -> None:
        """Handle Solve All button click."""
        # Prevent multiple clicks
        if self.running:
            print("Already solving...")
            return
        
        if self.gen is None:
            self.gen = self.csp.backtrack_generator()
        
        self.running = True
        self.solve_all_mode = True
        self.btn_solve.label.set_text("Solving...")
        self.btn_solve.ax.set_facecolor(BUTTON_ACTIVE_COLOR)
        self.fig.canvas.draw_idle()
        print("Starting fast solve...")
        
        event_count = [0]
        
        def animate(frame: int) -> None:
            if not self.running:
                if self.animation:
                    self.animation.event_source.stop()
                    self.animation = None
                return
            
            # Process multiple events per frame for speed
            for _ in range(EVENTS_PER_FRAME):
                try:
                    ev = next(self.gen)
                    self.handle_event(ev)
                    event_count[0] += 1
                except StopIteration:
                    self.running = False
                    self.solve_all_mode = False
                    self.btn_solve.label.set_text("Solve All")
                    self.btn_solve.ax.set_facecolor(BUTTON_DEFAULT_COLOR)
                    self.draw_board()
                    self.update_metrics()
                    if self.animation:
                        self.animation.event_source.stop()
                        self.animation = None
                    print(f"✓ Solve complete! Processed {event_count[0]} events")
                    return
            
            # Update display every batch of events
            self.draw_board()
            self.update_metrics()
        
        self.animation = FuncAnimation(
            self.fig, animate, interval=1, 
            cache_frame_data=False, repeat=False
        )
        plt.draw()
    
    def on_speed(self, val: float) -> None:
        self.speed = val
    
    def on_new_puzzle(self, event: Any) -> None:
        self.initial_board = generate_puzzle(self.size, difficulty='Easy')
        if self.animation:
            self.animation.event_source.stop()
        self.reset()