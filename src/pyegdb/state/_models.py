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

"""Core data models for EGDB positions and materials."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Material:
    """Piece counts for an endgame position."""

    bk: int = 0
    wk: int = 0
    bm: int = 0
    wm: int = 0

    @property
    def total_pieces(self) -> int:
        return self.bk + self.wk + self.bm + self.wm

    @property
    def total_men(self) -> int:
        return self.bm + self.wm

    @property
    def total_kings(self) -> int:
        return self.bk + self.wk

    def __str__(self) -> str:
        return f"{self.bk}bk, {self.wk}wk, {self.bm}bm, {self.wm}wm"


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable checkerboard position with canonically sorted squares."""

    bk: tuple[int, ...] = ()
    wk: tuple[int, ...] = ()
    bm: tuple[int, ...] = ()
    wm: tuple[int, ...] = ()

    def __init__(
        self,
        *,
        bk: tuple[int, ...] | list[int] = (),
        wk: tuple[int, ...] | list[int] = (),
        bm: tuple[int, ...] | list[int] = (),
        wm: tuple[int, ...] | list[int] = (),
    ) -> None:
        object.__setattr__(self, "bk", tuple(sorted(bk)))
        object.__setattr__(self, "wk", tuple(sorted(wk)))
        object.__setattr__(self, "bm", tuple(sorted(bm)))
        object.__setattr__(self, "wm", tuple(sorted(wm)))

    @property
    def material(self) -> Material:
        return Material(
            bk=len(self.bk),
            wk=len(self.wk),
            bm=len(self.bm),
            wm=len(self.wm),
        )

    @property
    def lead_black(self) -> int | None:
        """Highest rank occupied by any black man (0-based), or None if no black men."""
        if not self.bm:
            return None
        from pyegdb.layout import SQ_PER_ROW

        return max((sq - 1) // SQ_PER_ROW for sq in self.bm)

    @property
    def lead_white(self) -> int | None:
        """Highest rank occupied by any white man from White's perspective (0-based), or None."""
        if not self.wm:
            return None
        from pyegdb.layout import DIMENSION, SQ_PER_ROW

        return max(DIMENSION - 1 - (sq - 1) // SQ_PER_ROW for sq in self.wm)

    def __str__(self) -> str:
        def _fmt(cells: tuple[int, ...]) -> str:
            return ",".join(str(c) for c in cells)

        return (
            f"bk=[{_fmt(self.bk)}] "
            f"wk=[{_fmt(self.wk)}] "
            f"bm=[{_fmt(self.bm)}] "
            f"wm=[{_fmt(self.wm)}]"
        )
