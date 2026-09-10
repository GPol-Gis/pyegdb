# vim: set ft=python et sw=4 ts=4:

# pyegdb - Dense combinatorial indexing for checkers endgames
# Copyright (C) 2026 Dickson Duah <newleaf.dd@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Board layout shared by endgame-database components.

Defines board geometry, playable-square count, starting-piece limits,
and coordinate transformations.

Playable squares are numbered from 1 through ``SQ_COUNT``.
Rows and columns are zero-based internally.

Supported boards:
-----------------
8x8 (English / American checkers):
    4 playable squares per row -> 32 playable squares, 12 pieces per side.

10x10 (International / Polish draughts):
    5 playable squares per row -> 50 playable squares, 20 pieces per side.
"""

from __future__ import annotations

import threading
from enum import IntEnum
from typing import TYPE_CHECKING, Final, final

# ---------------------------------------------------------------------------
# Board size enumeration
# ---------------------------------------------------------------------------


@final
class BoardLayout(IntEnum):
    """Supported draughts / checkers board sizes."""

    ENGLISH = 8
    """Standard English / American checkerboard (8x8)."""

    INTERNATIONAL = 10
    """International / Polish draughts board (10x10)."""

    __module__ = "pyegdb.layout"


# ---------------------------------------------------------------------------
# Private geometry engine
# ---------------------------------------------------------------------------


@final
class _BoardLayoutGeometry:
    """Internal mutable geometry calculator (process-wide singleton)."""

    __slots__ = ("_lock", "_size")

    def __init__(self) -> None:
        self._lock: Final = threading.RLock()
        self._size: int = 0

    def initialize(self, board_size: BoardLayout) -> None:
        with self._lock:
            if self._size and self._size != board_size.value:
                raise RuntimeError(
                    f"Geometry already initialised with size={self._size}. "
                    "Call debug_reset() only from tests if reconfiguration is required."
                )
            self._size = board_size.value

    def _require_ready(self) -> None:
        if not self._size:
            raise RuntimeError(
                "Board geometry has not been initialised. "
                "Call setsize(BoardSize.ENGLISH) or "
                "setsize(BoardSize.INTERNATIONAL) first."
            )

    @property
    def dimension(self) -> int:
        """Board dimension."""
        self._require_ready()
        return self._size

    @property
    def dark_per_row(self) -> int:
        return self.dimension // 2

    @property
    def dark_count(self) -> int:
        return self.dark_per_row * self.dimension

    @property
    def starting_rows(self) -> int:
        return (self.dimension - 2) // 2

    @property
    def starting_pieces(self) -> int:
        return self.starting_rows * self.dark_per_row

    def row_index(self, square: int) -> int:
        self.check_square(square)
        return (square - 1) // self.dark_per_row

    def column_index(self, square: int) -> int:
        self.check_square(square)
        return (square - 1) % self.dark_per_row

    def forward_rank(self, square: int) -> int:
        return self.row_index(square)

    def reverse_rank(self, square: int) -> int:
        return self.dimension - 1 - self.row_index(square)

    def flip_vertical(self, square: int) -> int:
        row = self.row_index(square)
        col = self.column_index(square)
        return (self.dimension - 1 - row) * self.dark_per_row + col + 1

    def flip_horizontal(self, square: int) -> int:
        row = self.row_index(square)
        col = self.column_index(square)
        return row * self.dark_per_row + (self.dark_per_row - 1 - col) + 1

    def check_square(self, square: int) -> None:
        self._require_ready()
        if not 1 <= square <= self.dark_count:
            raise ValueError(f"square must be in 1..{self.dark_count}, got {square}")

    def reset_for_tests(self) -> None:
        with self._lock:
            self._size = 0

    def __repr__(self) -> str:
        if not self._size:
            return "BoardLayoutGeometry(<uninitialised>)"
        return f"BoardLayoutGeometry({self._size}x{self._size})"


# ---------------------------------------------------------------------------
# Process-wide singleton
# ---------------------------------------------------------------------------

_geometry: Final[_BoardLayoutGeometry] = _BoardLayoutGeometry()


# ---------------------------------------------------------------------------
# Module-level constants (dynamically resolved from _geometry singleton)
# ---------------------------------------------------------------------------

_LAYOUT_CONSTANTS: Final[dict[str, str]] = {
    "DIMENSION": "dimension",  # D
    "SQ_PER_ROW": "dark_per_row",  # N
    "SQ_COUNT": "dark_count",  # S
    "STARTING_ROWS": "initial_rows",
    "STARTING_PIECES": "max_pieces",
}

if TYPE_CHECKING:
    DIMENSION: int
    """Board side length (8 or 10)."""

    SQ_PER_ROW: int
    """Playable (dark) squares per row (4 or 5)."""

    SQ_COUNT: int
    """Total number of playable squares (32 or 50)."""

    STARTING_ROWS: int
    """Rows occupied by each side at the start of a game."""

    STARTING_PIECES: int
    """Maximum starting pieces for one player (12 or 20)."""


def __getattr__(name: str) -> int:
    if name in _LAYOUT_CONSTANTS:
        attr_name = _LAYOUT_CONSTANTS[name]
        return int(getattr(_geometry, attr_name))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + list(_LAYOUT_CONSTANTS.keys()))


# ---------------------------------------------------------------------------
# Public control functions
# ---------------------------------------------------------------------------


def initialize(*, layout: BoardLayout) -> None:
    """Initialise the process-wide board geometry."""
    _geometry.initialize(layout)


def is_initialized() -> bool:
    """Return True when layout has been initialized."""
    return _geometry._size != 0


def debug_reset() -> None:
    """Restore uninitialised state (unit tests only)."""
    _geometry.reset_for_tests()


# ---------------------------------------------------------------------------
# Coordinate transforms
# ---------------------------------------------------------------------------


def row_index(square: int) -> int:
    """Zero-based row containing *square*."""
    return _geometry.row_index(square)


def column_index(square: int) -> int:
    """Zero-based column of *square* inside its row."""
    return _geometry.column_index(square)


def forward_rank(square: int) -> int:
    """Distance from the forward back-rank."""
    return _geometry.forward_rank(square)


def reverse_rank(square: int) -> int:
    """Distance from the opposite back-rank."""
    return _geometry.reverse_rank(square)


def flip_vertical(square: int) -> int:
    """Vertically mirrored square (reflection across the horizontal mid-line)."""
    return _geometry.flip_vertical(square)


def flip_horizontal(square: int) -> int:
    """Horizontally mirrored square (reflection across the vertical mid-line)."""
    return _geometry.flip_horizontal(square)


def check_square(square: int) -> None:
    """Raise ValueError if *square* lies outside the legal range [1, SQ_COUNT]."""
    _geometry.check_square(square)
