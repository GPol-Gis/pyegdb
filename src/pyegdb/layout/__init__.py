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

"""Public layout API for pyegdb."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._layout import (
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

if TYPE_CHECKING:
    from ._layout import (
        DIMENSION,
        SQ_COUNT,
        SQ_PER_ROW,
        STARTING_PIECES,
        STARTING_ROWS,
    )

__all__ = [  # noqa: RUF022
    # Type
    "BoardLayout",
    # Constants
    "DIMENSION",
    "SQ_COUNT",
    "SQ_PER_ROW",
    "STARTING_PIECES",
    "STARTING_ROWS",
    # Coordinate transform
    "check_square",
    "column_index",
    "flip_horizontal",
    "flip_vertical",
    "forward_rank",
    "is_initialized",
    "reverse_rank",
    "row_index",
    # Configuration
    "initialize",
    "debug_reset",
]


def __getattr__(name: str) -> Any:
    from . import _layout

    if name in _layout._LAYOUT_CONSTANTS:
        return getattr(_layout, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
