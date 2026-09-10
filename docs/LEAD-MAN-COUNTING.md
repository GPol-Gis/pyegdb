# Lead Man Counting

```Python
from __future__ import annotations

from functools import cache

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
    """
    Return the size of a material block.

    A material block fixes the number of black men occupying the black
    back row. The remaining black men are placed in the interior domain,
    followed by the white men in the squares not occupied by black men.

    Parameters
    ----------
    material:
        Material composition being enumerated.
    black_back_count:
        Number of black men occupying the black back row.
    king_factor:
        Number of possible king placements for this material.

    Returns
    -------
    int
        Number of positions in the block.
    """
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
    """
    Return the total configuration-space size for ``material``.

    The space is partitioned according to the number of black men on
    the black back row. Each partition is independently ranked and
    therefore contributes one material block.
    """
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
    """
    Return the number of rows shared by the black and white rank regions.

    ``black_rank`` measures black advancement from the black home row.
    ``white_rank`` measures white advancement from the white home row.

    For a board of dimension ``D``, the overlap begins when:

        black_rank + white_rank >= D - 1

    and its height is therefore:

        max(0, black_rank + white_rank - D + 2)
    """
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


# ============================================================================
# Rank-Constrained Men Counting
# ============================================================================


def count_men_overlap(
    black_count: int,
    white_count: int,
    black_rank: int,
    white_rank: int,
) -> int:
    """
    Count men placements subject to both advancement ranks.

    The two rank regions may overlap. When they do, black and white men
    compete for the same squares, so the placements cannot be counted
    independently.

    The calculation proceeds by conditioning on the number of white men
    occupying the white leading row.

    For each such choice:

    ``k = white_count - leading_white``

        is the number of remaining white men.

    ``A = A0 - leading_white``

        is the remaining black-side non-overlap capacity.

    The black men that cannot be placed in ``A`` must occupy the
    obstruction region consisting of:

        black leading row + pure overlap rows.

    Let ``obstruct`` denote that number.

    Its feasible interval is determined by four constraints:

        1 <= obstruct
        obstruct <= black_count
        black_count - A <= obstruct
        obstruct <= white_capacity - k
        obstruct <= obstruction_region_size

    For a fixed ``obstruct``:

    * ``C(N + M, obstruct) - C(M, obstruct)``

      chooses the obstruction squares while requiring at least one
      black man to occupy the black leading row;

    * ``C(A, black_count - obstruct)``

      places the remaining black men;

    * ``C(white_capacity - obstruct, k)``

      places the remaining white men.

    The total is the sum over all valid leading-row and obstruction
    counts.

    Parameters
    ----------
    black_count:
        Number of black men.
    white_count:
        Number of white men.
    black_rank:
        Maximum black advancement rank.
    white_rank:
        Maximum white advancement rank.

    Returns
    -------
    int
        Number of admissible men-only configurations.
    """
    dimension = layout.DIMENSION
    row_width = layout.SQ_PER_ROW

    # Number of squares in the pure overlap region.
    overlap_size = overlap_rows(black_rank, white_rank) * row_width

    # White-side capacity before black obstruction.
    white_capacity = white_rank * row_width

    # Black-side area before removing white leading-row squares.
    black_area = (dimension - white_rank) * row_width

    total = 0

    max_leading_white = min(
        row_width,
        white_count,
    )

    for leading_white in range(
        1,
        max_leading_white + 1,
    ):
        remaining_white = white_count - leading_white

        # White leading-row men occupy squares that would otherwise
        # be available to black.
        available_black = black_area - leading_white

        # Determine how many black men must occupy the obstruction
        # region.
        min_obstruct = max(
            1,
            black_count - available_black,
        )

        max_obstruct = min(
            black_count,
            white_capacity - remaining_white,
            row_width + overlap_size,
        )

        for obstruct in range(
            min_obstruct,
            max_obstruct + 1,
        ):
            remaining_black = black_count - obstruct

            # Choose obstruction squares while requiring at least one
            # square from the black leading row.
            obstruction_ways = choose(
                row_width + overlap_size,
                obstruct,
            ) - choose(
                overlap_size,
                obstruct,
            )

            black_ways = choose(
                available_black,
                remaining_black,
            )

            white_ways = choose(
                white_capacity - obstruct,
                remaining_white,
            )

            total += (
                choose(row_width, leading_white)
                * obstruction_ways
                * black_ways
                * white_ways
            )

    return total


# ============================================================================
# Reference Implementation
# ============================================================================


@cache
def overlap_count(
    overlap_size: int,
    black_capacity: int,
    white_capacity: int,
    black_count: int,
    white_count: int,
    black_lead_count: int,
    white_lead_count: int,
) -> int:
    """
    Evaluate the original overlap convolution for fixed lead-row counts.

    This function is retained as a reference implementation for validating
    alternative formulations of the overlap calculation.

    The summation variable ``overlap_black`` represents the number of black
    men placed in the pure overlap region.

    Mathematically:

        Σ_b C(M, b)
            C(A, bm - i - b)
            C(B - b, wm - j)

    over all feasible ``b``.
    """
    remaining_black = black_count - black_lead_count
    remaining_white = white_count - white_lead_count

    lower = max(
        0,
        remaining_black - black_capacity,
    )

    upper = min(
        overlap_size,
        remaining_black,
        white_capacity - remaining_white,
    )

    return sum(
        choose(overlap_size, overlap_black)
        * choose(
            black_capacity,
            remaining_black - overlap_black,
        )
        * choose(
            white_capacity - overlap_black,
            remaining_white,
        )
        for overlap_black in range(lower, upper + 1)
    )


def count_men_overlap_classic(
    black_count: int,
    white_count: int,
    black_rank: int,
    white_rank: int,
) -> int:
    """
    Reference implementation using explicit lead-row decomposition.

    This implementation is useful for validating :func:`count_men_overlap`.
    It should not be used as the primary implementation unless the
    convolution-based formulation is specifically required.
    """
    row_width = layout.SQ_PER_ROW

    overlap_size = overlap_rows(black_rank, white_rank) * row_width

    total = 0

    for black_lead_count in range(
        1,
        min(row_width, black_count) + 1,
    ):
        for white_lead_count in range(
            1,
            min(row_width, white_count) + 1,
        ):
            lead_ways = choose(row_width, black_lead_count) * choose(
                row_width, white_lead_count
            )

            black_capacity = (
                layout.DIMENSION - white_rank
            ) * row_width - white_lead_count

            white_capacity = white_rank * row_width - black_lead_count

            total += lead_ways * overlap_count(
                overlap_size,
                black_capacity,
                white_capacity,
                black_count,
                white_count,
                black_lead_count,
                white_lead_count,
            )

    return total
```
