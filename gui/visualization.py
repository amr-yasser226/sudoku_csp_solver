from __future__ import annotations
from typing import Any

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# Type alias
PuzzleBoard = list[list[int]]


# Color schemes
COLORS = {
    'board_light': '#ffffff',
    'board_dark': '#f5f5f5',
    'grid_thin': '#cccccc',
    'grid_thick': '#000000',
    'initial_number': '#000000',
    'solved_number': '#0066cc',
    'highlight_try': '#ff6b6b',
    'highlight_success': '#51cf66',
    'domain_text': '#888888'
}


def draw_sudoku_grid(ax: plt.Axes, size: int, box_size: int) -> None:
    ax.clear()
    ax.set_xlim(0, size)
    ax.set_ylim(0, size)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal')
    
    # Draw cells
    for r in range(size):
        for c in range(size):
            ax.add_patch(patches.Rectangle(
                (c, size - r - 1), 1, 1,
                facecolor=COLORS['board_light'],
                edgecolor=COLORS['grid_thin'],
                linewidth=0.5
            ))
    
    # Draw thick box borders
    for i in range(0, size + 1, box_size):
        ax.axhline(i, color=COLORS['grid_thick'], linewidth=2)
        ax.axvline(i, color=COLORS['grid_thick'], linewidth=2)


def draw_number(
    ax: plt.Axes, 
    row: int, 
    col: int, 
    value: int, 
    size: int, 
    initial: bool = True
) -> None:
    color = COLORS['initial_number'] if initial else COLORS['solved_number']
    weight = 'bold' if initial else 'normal'
    
    ax.text(
        col + 0.5, size - row - 1 + 0.5, str(value),
        fontsize=20, ha='center', va='center',
        color=color, weight=weight
    )


def draw_domain_size(ax: plt.Axes, row: int, col: int, domain_size: int, size: int) -> None:
    if domain_size > 0:
        ax.text(
            col + 0.1, size - row - 0.9, f'{domain_size}',
            fontsize=7, color=COLORS['domain_text']
        )


def highlight_cell(ax: plt.Axes, row: int, col: int, size: int, success: bool = False) -> None:
    color = COLORS['highlight_success'] if success else COLORS['highlight_try']
    
    ax.add_patch(patches.Rectangle(
        (col, size - row - 1), 1, 1,
        fill=False,
        edgecolor=color,
        linewidth=3
    ))


def draw_domain_possibilities(
    ax: plt.Axes, 
    row: int, 
    col: int, 
    domain_values: list[int], 
    size: int
) -> None:
    # Only show if domain is small (2-4 values)
    if 2 <= len(domain_values) <= 4:
        text = ','.join(map(str, domain_values))
        ax.text(
            col + 0.5, size - row - 0.5, text,
            fontsize=6, ha='center', va='center',
            color=COLORS['domain_text'], alpha=0.7
        )


def create_metrics_text(
    csp: Any, 
    assignment: dict[tuple[int, int], int], 
    status: str, 
    mrv_var: tuple[int, int] | None = None, 
    domain_size: int | None = None
) -> str:
    total_vars = len(csp.variables)
    assigned = len(assignment)
    progress = (assigned / total_vars * 100) if total_vars > 0 else 0
    
    lines = [
        f"Sudoku {csp.size}x{csp.size}",
        f"Variables: {total_vars}",
        f"Assigned: {assigned} / {total_vars} ({progress:.1f}%)",
        "",
        f"Nodes visited: {csp.nodes}",
        f"Backtracks: {csp.backtracks}",
        f"Solutions found: {csp.solutions}",
        "",
    ]
    
    if mrv_var:
        lines.append(f"Current variable (MRV): {mrv_var}")
        lines.append(f"Domain size: {domain_size if domain_size else '-'}")
    else:
        lines.append("Current variable (MRV): -")
        lines.append("Domain size: -")
    
    lines.append("")
    lines.append(f"Status: {status}")
    
    # Add efficiency metrics
    if csp.nodes > 0:
        efficiency = (1 - csp.backtracks / csp.nodes) * 100
        lines.append(f"Efficiency: {efficiency:.1f}%")
    
    return "\n".join(lines)


def save_board_image(ax: plt.Axes, filename: str = 'sudoku_solution.png', dpi: int = 150) -> None:
    fig = ax.get_figure()
    if fig:
        fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Board saved to {filename}")


def animate_solution_path(boards: list[PuzzleBoard], delay: float = 0.5) -> None:
    if not boards:
        return
    
    size = len(boards[0])
    box_size = int(np.sqrt(size))
    
    fig, ax = plt.subplots(figsize=(8, 8))
    
    for board in boards:
        draw_sudoku_grid(ax, size, box_size)
        
        # Draw numbers
        for r in range(size):
            for c in range(size):
                if board[r][c] != 0:
                    draw_number(ax, r, c, board[r][c], size)
        
        plt.pause(delay)
        
    plt.show()


def export_to_ascii(board: PuzzleBoard) -> str:
    if not board:
        return ""
    
    size = len(board)
    box_size = int(np.sqrt(size))
    
    lines = []
    lines.append("┌" + "─" * (size * 2 + box_size - 1) + "┐")
    
    for r in range(size):
        row_str = "│"
        for c in range(size):
            val = board[r][c]
            row_str += str(val) if val != 0 else "·"
            
            if (c + 1) % box_size == 0 and c < size - 1:
                row_str += "│"
            else:
                row_str += " "
        
        row_str = row_str.rstrip() + "│"
        lines.append(row_str)
        
        # Horizontal separator for boxes
        if (r + 1) % box_size == 0 and r < size - 1:
            lines.append("├" + "─" * (size * 2 + box_size - 1) + "┤")
    
    lines.append("└" + "─" * (size * 2 + box_size - 1) + "┘")
    
    return "\n".join(lines)


def print_board(board: PuzzleBoard, title: str = "Sudoku Board") -> None:
    print(f"\n{title}")
    print(export_to_ascii(board))