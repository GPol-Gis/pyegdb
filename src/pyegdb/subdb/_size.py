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

from .combinatorics import (
    choose,
    king_radix,
)


def king_radix_size(material: state.Material) -> int:
    """Return the number of possible king placements for ``material``."""
    return king_radix(material, layout.SQ_COUNT)


def material_block_size(
    material: state.Material,
    black_back_count: int,
    king_factor: int,
) -> int:
    square_count = layout.SQ_COUNT
    row_width = layout.SQ_PER_ROW

    black_interior_count = material.bm - black_back_count

    black_back_ways = choose(row_width, black_back_count)
    black_interior_ways = choose(
        square_count - 2 * row_width,
        black_interior_count,
    )

    white_domain_size = square_count - row_width - black_interior_count
    white_ways = choose(white_domain_size, material.wm)

    return king_factor * black_back_ways * black_interior_ways * white_ways


def material_space_size(material: state.Material) -> int:
    row_width = layout.SQ_PER_ROW
    king_factor = king_radix_size(material)

    max_back_count = min(material.bm, row_width)

    return sum(
        material_block_size(
            material,
            black_back_count,
            king_factor,
        )
        for black_back_count in range(max_back_count + 1)
    )


def overlap_rows(
    black_rank: int,
    white_rank: int,
) -> int:
    dimension = layout.DIMENSION

    return max(
        0,
        black_rank + white_rank - dimension + 2,
    )


def men_combinations(
    man_count: int,
    man_rank: int,
) -> int:
    """
    Count placements of ``man_count`` men constrained by ``man_rank``.

    A side whose maximum advancement rank is ``man_rank`` may occupy
    ``man_rank + 1`` rows, but must occupy its leading row at least once.

    Hence:

        C((rank + 1)N, count) - C(rank N, count)

    where ``N`` is the number of playable squares per row.
    """
    assert man_count, "man_count must be non-zero"

    row_width = layout.SQ_PER_ROW

    return choose(
        (man_rank + 1) * row_width,
        man_count,
    ) - choose(
        man_rank * row_width,
        man_count,
    )


def count_men_overlap(
    black_count: int,
    white_count: int,
    black_rank: int,
    white_rank: int,
) -> int:
    dimension = layout.DIMENSION
    row_width = layout.SQ_PER_ROW

    ho = overlap_rows(black_rank, white_rank)
    if ho < 2:
        raise ValueError(f"count_men_overlap expects overlap >= 2, got {ho}")

    A = (dimension - 1 - white_rank) * row_width
    B = (dimension - 1 - black_rank) * row_width
    M = (ho - 2) * row_width

    total = 0
    for i in range(1, min(black_count, row_width) + 1):
        for j in range(1, min(white_count, row_width) + 1):
            lead_ways = choose(row_width, i) * choose(row_width, j)
            rem_b = black_count - i
            rem_w = white_count - j
            sum_b = 0
            for b_m in range(min(rem_b, M) + 1):
                sum_b += (
                    choose(M, b_m)
                    * choose(A + row_width - j, rem_b - b_m)
                    * choose(B + row_width - i + M - b_m, rem_w)
                )
            total += lead_ways * sum_b

    return total


def men_rank_combinations(
    material: state.Material,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    black_count = material.bm
    white_count = material.wm

    if black_count == 0 and white_count == 0:
        return 1

    if black_count == 0:
        return men_combinations(
            white_count,
            white_man_rank,
        )

    if white_count == 0:
        return men_combinations(
            black_count,
            black_man_rank,
        )

    overlap = overlap_rows(
        black_man_rank,
        white_man_rank,
    )

    if overlap == 0:
        return men_combinations(
            black_count,
            black_man_rank,
        ) * men_combinations(
            white_count,
            white_man_rank,
        )

    if overlap == 1:
        row_width = layout.SQ_PER_ROW

        black_non_lead_area = black_man_rank * row_width
        white_non_lead_area = white_man_rank * row_width

        return sum(
            choose(row_width, black_lead_count)
            * choose(
                black_non_lead_area,
                black_count - black_lead_count,
            )
            * (
                choose(
                    white_non_lead_area + row_width - black_lead_count,
                    white_count,
                )
                - choose(
                    white_non_lead_area,
                    white_count,
                )
            )
            for black_lead_count in range(
                1,
                min(black_count, row_width) + 1,
            )
        )

    return count_men_overlap(
        black_count,
        white_count,
        black_man_rank,
        white_man_rank,
    )


def size(
    material: state.Material,
    *,
    black_man_rank: int | None = None,
    white_man_rank: int | None = None,
) -> int:
    if black_man_rank is None and white_man_rank is None:
        return material_space_size(material)

    bl = black_man_rank if black_man_rank is not None else 0
    wl = white_man_rank if white_man_rank is not None else 0

    return king_radix_size(
        material,
    ) * men_rank_combinations(
        material,
        bl,
        wl,
    )
