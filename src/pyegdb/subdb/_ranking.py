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

"""
Ranking of material configurations and rank-constrained (lead-men) placements.
"""

from __future__ import annotations

from pyegdb import layout, state

from ._size import (
    king_radix_size,
    material_block_size,
    men_combinations,
    overlap_rows,
)
from .combinatorics import choose, colex_rank, rank_kings

# =============================================================================
# Unconstrained material ranking
# =============================================================================


def _rank_black_men(position: state.Position) -> tuple[int, int]:
    """
    Rank the black-men placement.

    Black men are partitioned into

    * the black home row (squares 1 ... row_width), and
    * the interior (the remaining playable squares).

    The hierarchical index is

        black_index = interior_index · C(row_width, back_count) + back_index.

    Returns
    -------
    (black_index, back_count)
    """
    row_width = layout.SQ_PER_ROW
    interior_size = layout.SQ_COUNT - 2 * row_width

    back_squares = [s for s in position.bm if s <= row_width]
    interior_squares = [s for s in position.bm if s > row_width]

    back_count = len(back_squares)
    back_index = colex_rank([s - 1 for s in back_squares], n=row_width)
    interior_index = colex_rank(
        [s - 1 - row_width for s in interior_squares],
        n=interior_size,
    )

    black_index = interior_index * choose(row_width, back_count) + back_index
    return black_index, back_count


def _rank_white_men(
    position: state.Position,
    occupied_by_black: set[int],
) -> tuple[int, int]:
    """
    Rank white men inside the domain that remains after black men are placed.

    The domain is reversed before colex ranking so that the ordering agrees
    with the corresponding unranking routine.

    Returns
    -------
    (white_index, domain_size)
    """
    row_width = layout.SQ_PER_ROW

    domain = [
        s
        for s in range(row_width + 1, layout.SQ_COUNT + 1)
        if s not in occupied_by_black
    ]
    domain_size = len(domain)
    domain_index = {s: i for i, s in enumerate(domain)}

    # reverse the coordinates so that colex matches the unrank order
    reversed_coords = [domain_size - 1 - domain_index[s] for s in position.wm]
    white_index = colex_rank(reversed_coords, n=domain_size)
    return white_index, domain_size


def rank_unconstrained(position: state.Position) -> int:
    """
    Rank a complete material configuration in the unconstrained space.

    The global index is assembled hierarchically:

        block_offset
          + (black_index · C(white_domain, wm) + white_index) · king_factor
          + king_index

    Blocks are ordered from the largest possible black-home-row occupancy
    down to the occupancy of the given position.
    """
    material = position.material
    king_factor = king_radix_size(material)
    row_width = layout.SQ_PER_ROW

    # black men
    black_index, back_count = _rank_black_men(position)
    max_back = min(material.bm, row_width)

    block_offset = sum(
        material_block_size(material, candidate, king_factor)
        for candidate in range(max_back, back_count, -1)
    )

    # white men
    black_set = set(position.bm)
    if material.wm:
        white_index, white_domain_size = _rank_white_men(position, black_set)
    else:
        white_index = 0
        white_domain_size = layout.SQ_COUNT - row_width - (material.bm - back_count)

    # kings
    occupied = black_set | set(position.wm)
    king_index = (
        rank_kings(position.bk, position.wk, occupied, layout.SQ_COUNT)
        if material.bk or material.wk
        else 0
    )

    # assemble
    white_block = black_index * choose(white_domain_size, material.wm) + white_index
    return block_offset + white_block * king_factor + king_index


# =============================================================================
# Rank-constrained (lead-men) ranking
# =============================================================================


def _rank_single_side(
    men: tuple[int, ...] | list[int],
    man_rank: int,
    *,
    from_black: bool,
) -> int:
    """
    Rank a single colour that must occupy its leading row at least once.

    The allowed band contains (man_rank + 1) rows.  The returned index is

        C((rank+1)·W, count)  -  C(rank·W, count)

    expressed as a difference of two colex ranks, exactly matching
    :func:`men_combinations`.
    """
    count = len(men)
    if count == 0:
        return 0

    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION

    if from_black:
        # rows 0 ... man_rank
        domain = list(range(1, (man_rank + 1) * row_width + 1))
    else:
        # rows (dimension-1-man_rank) ... (dimension-1)
        domain = []
        for offset in range(man_rank + 1):
            row = dimension - 1 - offset
            domain.extend(range(row * row_width + 1, (row + 1) * row_width + 1))

    sq_to_idx = {sq: i for i, sq in enumerate(domain)}
    full_rank = colex_rank([sq_to_idx[s] for s in men], n=len(domain))
    non_lead_ways = choose(man_rank * row_width, count)
    return full_rank - non_lead_ways


def _rank_single_row_overlap(
    position: state.Position,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    """
    Rank when the two rank regions share exactly one row.

    The shared row is the black leading row (and simultaneously the white
    leading row).  Enumeration proceeds by the number of black men that
    occupy that row; the residual black and white placements are ranked
    independently inside their respective residual domains.
    """
    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION
    bm = position.material.bm
    wm = position.material.wm

    shared_row = black_man_rank
    shared = list(range(shared_row * row_width + 1, (shared_row + 1) * row_width + 1))
    black_non_lead = list(range(1, shared_row * row_width + 1))

    white_non_lead: list[int] = []
    for offset in range(white_man_rank):
        row = dimension - 1 - offset
        white_non_lead.extend(range(row * row_width + 1, (row + 1) * row_width + 1))

    black_on_shared = [s for s in position.bm if s in shared]
    black_elsewhere = [s for s in position.bm if s not in shared]
    lead_count = len(black_on_shared)

    # ranks inside the current cell
    lead_rank = colex_rank(
        [shared.index(s) for s in sorted(black_on_shared)], n=row_width
    )
    rest_rank = (
        colex_rank(
            [black_non_lead.index(s) for s in sorted(black_elsewhere)],
            n=black_man_rank * row_width,
        )
        if black_elsewhere
        else 0
    )

    free_on_shared = [s for s in shared if s not in black_on_shared]
    white_domain = white_non_lead + free_on_shared
    white_rank = colex_rank(
        [white_domain.index(s) for s in sorted(position.wm)],
        n=len(white_domain),
    ) - choose(white_man_rank * row_width, wm)

    # size of the residual black / white choices for this lead_count
    ways_rest = choose(black_man_rank * row_width, bm - lead_count)
    ways_white = choose(
        white_man_rank * row_width + row_width - lead_count, wm
    ) - choose(white_man_rank * row_width, wm)

    # accumulate all cells that precede the present lead_count
    offset = sum(
        choose(row_width, prev)
        * choose(black_man_rank * row_width, bm - prev)
        * (
            choose(white_man_rank * row_width + row_width - prev, wm)
            - choose(white_man_rank * row_width, wm)
        )
        for prev in range(1, lead_count)
    )

    return (
        offset
        + lead_rank * ways_rest * ways_white
        + rest_rank * ways_white
        + white_rank
    )


def _rank_general_overlap(
    position: state.Position,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    """
    Rank men when the rank regions overlap by two or more rows.

    The board is partitioned into five contiguous bands (from black home
    toward white home):

        A   - pure black non-overlap
        L_w - white leading row
        M   - pure overlap
        L_b - black leading row
        B   - pure white non-overlap

    Enumeration order (outer to inner):

        black-lead count  i  ≥ 1
        white-lead count  j  ≥ 1
        black men in M    b_M

    Inside a fixed (i, j, b_M) cell the four residual combinations are
    ranked in colex and combined by the mixed-radix product

        ((r_i · C(W,j) + r_j) · C(M,b_M) + r_M) · C(A', rem_b) + r_rest_b
        ) · C(B', rem_w) + r_rest_w
    """
    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION
    bm = position.material.bm
    wm = position.material.wm

    # band boundaries (1-based square numbers)
    white_lead_row = dimension - 1 - white_man_rank
    black_lead_row = black_man_rank

    band_A = list(range(1, white_lead_row * row_width + 1))
    band_Lw = list(
        range(
            white_lead_row * row_width + 1,
            (white_lead_row + 1) * row_width + 1,
        )
    )
    band_M = list(
        range(
            (white_lead_row + 1) * row_width + 1,
            black_lead_row * row_width + 1,
        )
    )
    band_Lb = list(
        range(
            black_lead_row * row_width + 1,
            (black_lead_row + 1) * row_width + 1,
        )
    )
    band_B = list(
        range(
            (black_lead_row + 1) * row_width + 1,
            dimension * row_width + 1,
        )
    )

    size_A = len(band_A)
    size_M = len(band_M)
    size_B = len(band_B)

    black_set = set(position.bm)
    white_set = set(position.wm)

    black_on_Lb = [s for s in position.bm if s in band_Lb]
    white_on_Lw = [s for s in position.wm if s in band_Lw]
    black_on_M = [s for s in position.bm if s in band_M]

    i = len(black_on_Lb)  # black-lead count
    j = len(white_on_Lw)  # white-lead count
    b_M = len(black_on_M)  # black men in pure overlap

    # offset = sum of sizes of all preceding cells
    def cell_size(ci: int, cj: int, cM: int) -> int:
        rem_black = bm - ci
        rem_white = wm - cj
        return (
            choose(row_width, ci)
            * choose(row_width, cj)
            * choose(size_M, cM)
            * choose(size_A + row_width - cj, rem_black - cM)
            * choose(size_M - cM + row_width - ci + size_B, rem_white)
        )

    offset = 0
    for ci in range(1, min(bm, row_width) + 1):
        for cj in range(1, min(wm, row_width) + 1):
            for cM in range(min(bm - ci, size_M) + 1):
                if ci == i and cj == j and cM == b_M:
                    break
                offset += cell_size(ci, cj, cM)
            else:
                continue
            break
        else:
            continue
        break

    # ranks inside the current cell
    rank_Lb = colex_rank([band_Lb.index(s) for s in black_on_Lb], n=row_width)
    rank_Lw = colex_rank([band_Lw.index(s) for s in white_on_Lw], n=row_width)
    rank_M = colex_rank([band_M.index(s) for s in black_on_M], n=size_M) if b_M else 0

    # residual black domain = A ∪ (free squares of Lw)
    free_Lw = [s for s in band_Lw if s not in white_set]
    black_rest_domain = band_A + free_Lw
    black_rest = [s for s in position.bm if s in black_rest_domain]
    rank_black_rest = (
        colex_rank(
            [black_rest_domain.index(s) for s in black_rest],
            n=len(black_rest_domain),
        )
        if black_rest
        else 0
    )

    # residual white domain = (free M) ∪ (free Lb) ∪ B
    free_M = [s for s in band_M if s not in black_set]
    free_Lb = [s for s in band_Lb if s not in black_set]
    white_rest_domain = free_M + free_Lb + band_B
    white_rest = [s for s in position.wm if s in white_rest_domain]
    rank_white_rest = (
        colex_rank(
            [white_rest_domain.index(s) for s in white_rest],
            n=len(white_rest_domain),
        )
        if white_rest
        else 0
    )

    # mixed-radix combination of the four residual ranks
    ways_Lw = choose(row_width, j)
    ways_M = choose(size_M, b_M)
    ways_black_rest = choose(len(black_rest_domain), bm - i - b_M)
    ways_white_rest = choose(len(white_rest_domain), wm - j)

    cell_rank = (
        ((rank_Lb * ways_Lw + rank_Lw) * ways_M + rank_M) * ways_black_rest
        + rank_black_rest
    ) * ways_white_rest + rank_white_rest

    return offset + cell_rank


def _rank_lead_men(
    position: state.Position,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    """
    Dispatch to the appropriate constrained ranking routine according to
    the overlap height of the two rank regions.
    """
    bm = position.material.bm
    wm = position.material.wm

    if bm == 0 and wm == 0:
        return 0
    if bm == 0:
        return _rank_single_side(position.wm, white_man_rank, from_black=False)
    if wm == 0:
        return _rank_single_side(position.bm, black_man_rank, from_black=True)

    overlap = overlap_rows(black_man_rank, white_man_rank)
    if overlap == 0:
        black_rank = _rank_single_side(position.bm, black_man_rank, from_black=True)
        white_rank = _rank_single_side(position.wm, white_man_rank, from_black=False)
        return black_rank * men_combinations(wm, white_man_rank) + white_rank

    if overlap == 1:
        return _rank_single_row_overlap(position, black_man_rank, white_man_rank)

    return _rank_general_overlap(position, black_man_rank, white_man_rank)


def rank_constrained(position: state.Position) -> int:
    """
    Full material rank under the advancement limits stored on the position.

    Layout (most-significant digit first):

        men_index · king_factor + king_index
    """
    material = position.material
    king_factor = king_radix_size(material)

    black_rank = getattr(position, "lead_black", None) or 0
    white_rank = getattr(position, "lead_white", None) or 0

    men_index = _rank_lead_men(position, black_rank, white_rank)

    occupied = set(position.bm) | set(position.wm)
    king_index = (
        rank_kings(position.bk, position.wk, occupied, layout.SQ_COUNT)
        if material.bk or material.wk
        else 0
    )
    return men_index * king_factor + king_index


# =============================================================================
# Public entry point
# =============================================================================


def rank(
    position: state.Position,
    *,
    constrain_by_lead_men: bool = False,
) -> int:
    """
    Rank a position.

    Parameters
    ----------
    position:
        The position to rank.
    constrain_by_lead_men:
        When false (default) the unconstrained material space is used.
        When true the advancement ranks ``position.lead_black`` /
        ``position.lead_white`` constrain the enumeration.
    """
    return (
        rank_constrained(position)
        if constrain_by_lead_men
        else rank_unconstrained(position)
    )
