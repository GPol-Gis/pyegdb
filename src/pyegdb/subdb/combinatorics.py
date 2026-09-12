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

"""Combinatorial utilities for EGDB indexing."""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache
from math import comb
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyegdb.state._models import Material


@cache
def choose(n: int, k: int) -> int:
    """Return the binomial coefficient C(n, k).

    Invalid combinations (k < 0, n < 0, k > n) return zero.
    """
    if n < 0 or k < 0 or k > n:
        return 0
    return comb(n, k)


def colex_rank(values: Sequence[int], n: int | None = None) -> int:
    """Return the colexicographic rank of a combination in 0..n-1."""
    if n is not None and any(v < 0 or v >= n for v in values):
        raise ValueError(f"coordinate out of range [0, {n}): {values}")

    return sum(comb(value, i) for i, value in enumerate(sorted(values), start=1))


def colex_unrank(rank: int, k: int, n: int) -> tuple[int, ...]:
    """Return the k-element combination with the given colex rank from 0..n-1."""
    if not 0 <= k <= n:
        raise ValueError(f"k must satisfy 0 <= k <= n, got k={k}, n={n}")

    count = comb(n, k)

    assert (
        0 <= rank < count
    ), f"rank must satisfy 0 <= rank < C({n}, {k})={count}, got {rank}"

    if k == 0:
        return ()

    result = [0] * k
    upper = n - 1

    for i in range(k, 0, -1):
        lower = i - 1
        best = lower

        while lower <= upper:
            middle = (lower + upper) // 2
            value = comb(middle, i)

            if value <= rank:
                best = middle
                lower = middle + 1
            else:
                upper = middle - 1

        result[i - 1] = best
        rank -= comb(best, i)
        upper = best - 1

    return tuple(result)


def colex_unrank_linear(rank: int, k: int, n: int):
    result = [0] * k
    upper = n - 1
    for i in range(k, 0, -1):
        # find largest x <= upper with C(x,i) <= rank
        while comb(upper, i) > rank:
            upper -= 1
        result[i - 1] = upper
        rank -= comb(upper, i)
        upper -= 1
    return tuple(result)


def king_radix(mat: Material, square_count: int) -> int:
    """Calculate the number of ways to place kings on remaining squares."""
    king_sqs = square_count - mat.bm - mat.wm
    return choose(king_sqs, mat.bk) * choose(king_sqs - mat.bk, mat.wk)


def rank_kings(
    bk_sqs: Sequence[int],
    wk_sqs: Sequence[int],
    occupied_sqs: set[int],
    square_count: int,
) -> int:
    """Rank kings on unoccupied dark squares."""
    king_domain = [sq for sq in range(1, square_count + 1) if sq not in occupied_sqs]
    pos_map = {sq: idx for idx, sq in enumerate(king_domain)}
    bk_coords = [pos_map[sq] for sq in bk_sqs]
    bk_rank = colex_rank(bk_coords, n=len(king_domain)) if bk_sqs else 0

    remaining = [sq for sq in king_domain if sq not in set(bk_sqs)]
    rem_pos_map = {sq: idx for idx, sq in enumerate(remaining)}
    wk_coords = [rem_pos_map[sq] for sq in wk_sqs]
    wk_rank = colex_rank(wk_coords, n=len(remaining)) if wk_sqs else 0

    wk_radix = choose(len(king_domain) - len(bk_sqs), len(wk_sqs))
    return bk_rank * wk_radix + wk_rank


def unrank_kings(
    king_rank: int,
    bk: int,
    wk: int,
    occupied_sqs: set[int],
    square_count: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Unrank kings on unoccupied dark squares."""
    king_domain = [sq for sq in range(1, square_count + 1) if sq not in occupied_sqs]
    wk_radix = choose(len(king_domain) - bk, wk)
    bk_rank = king_rank // wk_radix if wk_radix else 0
    wk_rank = king_rank % wk_radix if wk_radix else 0

    bk_coords = colex_unrank(bk_rank, bk, len(king_domain))
    bk_sqs = tuple(king_domain[i] for i in bk_coords)

    remaining = [sq for sq in king_domain if sq not in set(bk_sqs)]
    wk_coords = colex_unrank(wk_rank, wk, len(remaining))
    wk_sqs = tuple(remaining[i] for i in wk_coords)
    return bk_sqs, wk_sqs
