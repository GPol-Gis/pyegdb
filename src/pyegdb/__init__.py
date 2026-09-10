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

"""Checkers/Draughts Endgame Database (EGDB) package."""

from typing import TYPE_CHECKING, Any

from pyegdb import layout, state, subdb
from pyegdb.layout import (
    BoardLayout,
    check_square,
    column_index,
    debug_reset,
    flip_horizontal,
    flip_vertical,
    forward_rank,
    initialize,
    is_initialized,
    reverse_rank,
    row_index,
)
from pyegdb.state import Material, Position

if TYPE_CHECKING:
    from pyegdb.layout import (
        DIMENSION,
        SQ_COUNT,
        SQ_PER_ROW,
        STARTING_PIECES,
        STARTING_ROWS,
    )

__all__ = [  # noqa: RUF022
    # Submodules
    "layout",
    "state",
    # "io",
    "subdb",
    # Core Models
    "BoardLayout",
    "Material",
    "Position",
    # Constants
    "DIMENSION",
    "SQ_PER_ROW",
    "SQ_COUNT",
    "STARTING_PIECES",
    "STARTING_ROWS",
    # Functions
    "initialize",
    "is_initialized",
    "debug_reset",
    "check_square",
    "column_index",
    "flip_horizontal",
    "flip_vertical",
    "forward_rank",
    "reverse_rank",
    "row_index",
]


def __getattr__(name: str) -> Any:
    if hasattr(layout, name):
        return getattr(layout, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
