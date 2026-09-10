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

from __future__ import annotations

from pyegdb import layout, state

from ._size import (
    king_radix_size,
    material_block_size,
    men_combinations,
    overlap_rows,
)
from .combinatorics import (
    choose,
    colex_unrank,
    unrank_kings,
)


def _unrank_black_men(
    black_count: int,
    black_index: int,
    back_count: int,
) -> tuple[int, ...]:
    square_count = layout.SQ_COUNT
    row_width = layout.SQ_PER_ROW

    back_combination_count = choose(row_width, back_count)

    if back_combination_count:
        back_index = black_index % back_combination_count
        interior_index = black_index // back_combination_count
    else:
        back_index = 0
        interior_index = black_index

    back_squares = (
        [
            square + 1
            for square in colex_unrank(
                back_index,
                back_count,
                row_width,
            )
        ]
        if back_count
        else []
    )

    interior_count = black_count - back_count

    interior_squares = (
        [
            square + 1 + row_width
            for square in colex_unrank(
                interior_index,
                interior_count,
                square_count - 2 * row_width,
            )
        ]
        if interior_count
        else []
    )

    return tuple(sorted(back_squares + interior_squares))


def _unrank_white_men(
    white_count: int,
    white_index: int,
    black_men: tuple[int, ...],
) -> tuple[int, ...]:
    if white_count == 0:
        return ()

    square_count = layout.SQ_COUNT
    row_width = layout.SQ_PER_ROW

    black_set = set(black_men)

    domain = [
        square
        for square in range(row_width + 1, square_count + 1)
        if square not in black_set
    ]

    transformed = colex_unrank(
        white_index,
        white_count,
        len(domain),
    )

    domain_indices = [len(domain) - 1 - value for value in transformed]

    return tuple(sorted(domain[index] for index in domain_indices))


def unrank_unconstrained(
    material: state.Material,
    index: int,
) -> state.Position:
    square_count = layout.SQ_COUNT
    row_width = layout.SQ_PER_ROW
    king_factor = king_radix_size(material)

    remainder = index

    # Locate the black back-row-count block

    back_count = min(material.bm, row_width)

    for candidate in range(back_count, -1, -1):
        block = material_block_size(
            material,
            candidate,
            king_factor,
        )

        if block == 0:
            continue

        if remainder < block:
            back_count = candidate
            break

        remainder -= block
    else:
        raise IndexError("Index out of range")

    # Extract black, white and king ranks

    white_domain_size = square_count - row_width - (material.bm - back_count)

    black_block_size = choose(white_domain_size, material.wm) * king_factor

    if black_block_size:
        black_index = remainder // black_block_size
        remainder %= black_block_size
    else:
        black_index = 0

    if king_factor:
        white_index = remainder // king_factor
        king_index = remainder % king_factor
    else:
        white_index = 0
        king_index = 0

    # Reconstruct men

    black_men = _unrank_black_men(
        material.bm,
        black_index,
        back_count,
    )

    white_men = _unrank_white_men(
        material.wm,
        white_index,
        black_men,
    )

    occupied = set(black_men) | set(white_men)

    # Reconstruct kings

    black_kings, white_kings = unrank_kings(
        king_index,
        material.bk,
        material.wk,
        occupied,
        square_count,
    )

    return state.Position(
        bm=black_men,
        wm=white_men,
        bk=black_kings,
        wk=white_kings,
    )


def _unrank_single_side(
    count: int,
    index: int,
    man_rank: int,
    *,
    from_black: bool,
) -> tuple[int, ...]:
    """
    Inverse of `_rank_single_side`.
    """
    if count == 0:
        if index != 0:
            raise IndexError(f"index {index} out of range for count=0")
        return ()

    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION

    if from_black:
        domain = list(range(1, (man_rank + 1) * row_width + 1))
    else:
        domain = []
        for wr in range(man_rank + 1):
            row = dimension - 1 - wr
            domain.extend(range(row * row_width + 1, (row + 1) * row_width + 1))

    offset = choose(man_rank * row_width, count)
    total_ways = choose(len(domain), count) - offset
    if not (0 <= index < total_ways):
        raise IndexError(f"index {index} out of range [0, {total_ways})")

    idxs = colex_unrank(index + offset, count, len(domain))
    return tuple(sorted(domain[i] for i in idxs))


def _unrank_single_row_overlap(
    material: state.Material,
    index: int,
    black_man_rank: int,
    white_man_rank: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """
    Inverse of `_rank_single_row_overlap` for ho = 1.
    """
    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION
    bm, wm = material.bm, material.wm

    shared_row = black_man_rank
    shared_domain = list(
        range(shared_row * row_width + 1, (shared_row + 1) * row_width + 1)
    )
    b_non_lead_domain = list(range(1, shared_row * row_width + 1))

    w_non_lead_domain: list[int] = []
    for wr in range(white_man_rank):
        row = dimension - 1 - wr
        w_non_lead_domain.extend(range(row * row_width + 1, (row + 1) * row_width + 1))

    rem = index
    for i in range(1, min(bm, row_width) + 1):
        ways_rest = choose(black_man_rank * row_width, bm - i)
        ways_white = choose(white_man_rank * row_width + row_width - i, wm) - choose(
            white_man_rank * row_width, wm
        )
        ways = choose(row_width, i) * ways_rest * ways_white

        if rem < ways:
            lead_rk, rem = divmod(rem, ways_rest * ways_white)
            rest_rk, w_rk = divmod(rem, ways_white)

            b_lead = [shared_domain[idx] for idx in colex_unrank(lead_rk, i, row_width)]
            b_rest = (
                [
                    b_non_lead_domain[idx]
                    for idx in colex_unrank(rest_rk, bm - i, black_man_rank * row_width)
                ]
                if bm - i > 0
                else []
            )
            black_men = tuple(sorted(b_lead + b_rest))

            w_free_shared = [s for s in shared_domain if s not in set(b_lead)]
            w_domain = w_non_lead_domain + w_free_shared
            w_idxs = colex_unrank(
                w_rk + choose(white_man_rank * row_width, wm), wm, len(w_domain)
            )
            white_men = tuple(sorted(w_domain[idx] for idx in w_idxs))
            return black_men, white_men

        rem -= ways

    raise IndexError("index out of range (single-row overlap)")


def _unrank_general_overlap(
    material: state.Material,
    index: int,
    black_man_rank: int,
    white_man_rank: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """
    Inverse of `_rank_general_overlap` for ho >= 2.
    """
    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION
    bm, wm = material.bm, material.wm

    r_b = black_man_rank
    r_w = dimension - 1 - white_man_rank

    A_sqs = list(range(1, r_w * row_width + 1))
    A_size = len(A_sqs)
    L_w_sqs = list(range(r_w * row_width + 1, (r_w + 1) * row_width + 1))
    M_sqs = list(range((r_w + 1) * row_width + 1, r_b * row_width + 1))
    M_size = len(M_sqs)
    L_b_sqs = list(range(r_b * row_width + 1, (r_b + 1) * row_width + 1))
    B_sqs = list(range((r_b + 1) * row_width + 1, dimension * row_width + 1))
    B_size = len(B_sqs)

    def cell_ways(cur_i: int, cur_j: int, cur_bm: int) -> int:
        rem_b = bm - cur_i
        rem_w = wm - cur_j
        return (
            choose(row_width, cur_i)
            * choose(row_width, cur_j)
            * choose(M_size, cur_bm)
            * choose(A_size + row_width - cur_j, rem_b - cur_bm)
            * choose(M_size - cur_bm + row_width - cur_i + B_size, rem_w)
        )

    rem = index
    found = False
    for cur_i in range(1, min(bm, row_width) + 1):
        for cur_j in range(1, min(wm, row_width) + 1):
            for cur_bm in range(min(bm - cur_i, M_size) + 1):
                ways = cell_ways(cur_i, cur_j, cur_bm)
                if rem < ways:
                    i, j, b_m = cur_i, cur_j, cur_bm
                    found = True
                    break
                rem -= ways
            if found:
                break
        if found:
            break

    if not found:
        raise IndexError("index out of range (general overlap)")

    w4 = choose(M_size - b_m + row_width - i + B_size, wm - j)
    w3 = choose(A_size + row_width - j, bm - i - b_m)
    w2 = choose(M_size, b_m)
    w1 = choose(row_width, j)

    rem, r_w_rest = divmod(rem, w4)
    rem, r_b_rest = divmod(rem, w3)
    rem, r_b_m = divmod(rem, w2)
    r_b_lead, r_w_lead = divmod(rem, w1)

    b_lead = [L_b_sqs[idx] for idx in colex_unrank(r_b_lead, i, row_width)]
    w_lead = [L_w_sqs[idx] for idx in colex_unrank(r_w_lead, j, row_width)]
    b_m_sqs = (
        [M_sqs[idx] for idx in colex_unrank(r_b_m, b_m, M_size)] if b_m > 0 else []
    )

    L_w_free = [s for s in L_w_sqs if s not in set(w_lead)]
    b_rest_domain = A_sqs + L_w_free
    b_rest = (
        [
            b_rest_domain[idx]
            for idx in colex_unrank(r_b_rest, bm - i - b_m, len(b_rest_domain))
        ]
        if bm - i - b_m > 0
        else []
    )

    M_free = [s for s in M_sqs if s not in set(b_m_sqs)]
    L_b_free = [s for s in L_b_sqs if s not in set(b_lead)]
    w_rest_domain = M_free + L_b_free + B_sqs
    w_rest = (
        [
            w_rest_domain[idx]
            for idx in colex_unrank(r_w_rest, wm - j, len(w_rest_domain))
        ]
        if wm - j > 0
        else []
    )

    black_men = tuple(sorted(b_lead + b_m_sqs + b_rest))
    white_men = tuple(sorted(w_lead + w_rest))
    return black_men, white_men


def _unrank_lead_men(
    material: state.Material,
    index: int,
    black_man_rank: int,
    white_man_rank: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    bm, wm = material.bm, material.wm
    if index < 0:
        raise IndexError(f"index {index} must be non-negative")
    if bm == 0 and wm == 0:
        if index != 0:
            raise IndexError(f"index {index} out of range for empty men")
        return (), ()

    overlap = overlap_rows(black_man_rank, white_man_rank)

    if bm == 0:
        return (), _unrank_single_side(wm, index, white_man_rank, from_black=False)
    if wm == 0:
        return _unrank_single_side(bm, index, black_man_rank, from_black=True), ()

    if overlap == 0:
        b_ways = men_combinations(bm, black_man_rank)
        w_ways = men_combinations(wm, white_man_rank)
        total_ways = b_ways * w_ways
        if not (0 <= index < total_ways):
            raise IndexError(f"index {index} out of range [0, {total_ways})")
        b_idx, w_idx = divmod(index, w_ways)
        black_men = _unrank_single_side(bm, b_idx, black_man_rank, from_black=True)
        white_men = _unrank_single_side(wm, w_idx, white_man_rank, from_black=False)
        return black_men, white_men

    if overlap == 1:
        return _unrank_single_row_overlap(
            material, index, black_man_rank, white_man_rank
        )

    return _unrank_general_overlap(material, index, black_man_rank, white_man_rank)


def unrank_constrained(
    material: state.Material,
    index: int,
    black_man_rank: int,
    white_man_rank: int,
) -> state.Position:
    """Inverse of :func:`_rank_with_lead_men`."""
    if index < 0:
        raise IndexError(f"index {index} must be non-negative")
    king_factor = king_radix_size(material)
    men_index, king_index = divmod(index, king_factor)

    black_men, white_men = _unrank_lead_men(
        material, men_index, black_man_rank, white_man_rank
    )

    occupied = set(black_men) | set(white_men)
    black_kings, white_kings = unrank_kings(
        king_index,
        material.bk,
        material.wk,
        occupied,
        layout.SQ_COUNT,
    )
    return state.Position(
        bm=black_men,
        wm=white_men,
        bk=black_kings,
        wk=white_kings,
    )


def unrank(
    index: int,
    material: state.Material,
    *,
    black_man_rank: int | None = None,
    white_man_rank: int | None = None,
) -> state.Position:
    return (
        unrank_unconstrained(material, index)
        if (black_man_rank is None and white_man_rank is None)
        else unrank_constrained(
            material,
            index,
            black_man_rank if black_man_rank is not None else 0,
            white_man_rank if white_man_rank is not None else 0,
        )
    )
