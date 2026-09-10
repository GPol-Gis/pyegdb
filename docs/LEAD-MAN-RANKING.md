# Lead men ranking

```Python
# ============================================================================
# Rank-Constrained Men Ranking / Unranking
# ============================================================================


def _region_bounds(
    black_rank: int,
    white_rank: int,
) -> tuple[int, int, int, int, int, int]:
    """
    Compute the square intervals that define the constrained regions.

    Returns
    -------
    black_lead_lo, black_lead_hi,
    pure_overlap_lo, pure_overlap_hi,
    white_lead_lo, white_lead_hi
        Inclusive 1-based square bounds for each region.
    """
    dimension = layout.DIMENSION
    row_width = layout.SQ_PER_ROW

    # Black home is row 0; white home is row dimension-1.
    black_lead_row = black_rank
    white_lead_row = dimension - 1 - white_rank

    black_lead_lo = black_lead_row * row_width + 1
    black_lead_hi = black_lead_lo + row_width - 1

    white_lead_lo = white_lead_row * row_width + 1
    white_lead_hi = white_lead_lo + row_width - 1

    # Pure-overlap rows are the intersection of the two allowed bands.
    black_allowed_hi = black_rank
    white_allowed_lo = dimension - 1 - white_rank

    overlap_lo_row = max(0, white_allowed_lo)
    overlap_hi_row = min(dimension - 1, black_allowed_hi)

    if overlap_lo_row > overlap_hi_row:
        pure_overlap_lo = pure_overlap_hi = 0
    else:
        pure_overlap_lo = overlap_lo_row * row_width + 1
        pure_overlap_hi = (overlap_hi_row + 1) * row_width

    return (
        black_lead_lo,
        black_lead_hi,
        pure_overlap_lo,
        pure_overlap_hi,
        white_lead_lo,
        white_lead_hi,
    )


def rank_lead_men(
    position: state.Position,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    """
    Rank a men-only configuration under the given advancement-rank limits.

    The ranking follows exactly the same enumeration order that
    :func:`men_rank_combinations` / :func:`count_men_overlap` use for
    counting, guaranteeing that

        0 ≤ rank_lead_men(...) < men_rank_combinations(...)

    and that the map is bijective.

    Special cases (no men, single side, zero overlap, single-row overlap)
    are handled by the same dispatch logic that appears in
    :func:`men_rank_combinations`.  The general-overlap case decomposes
    the placement into:

        leading-white count  →  obstruction count  →  residual choices
    """
    material = position.material
    black_count = material.bm
    white_count = material.wm

    if black_count == 0 and white_count == 0:
        return 0

    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION

    # ------------------------------------------------------------------
    # Single-side cases – independent rank counting
    # ------------------------------------------------------------------
    if black_count == 0:
        # White men only: rank inside the white-allowed band,
        # forcing at least one man onto the white leading row.
        white_squares = sorted(position.wm)
        lead_row_lo = (dimension - 1 - white_man_rank) * row_width + 1
        lead_row_hi = lead_row_lo + row_width - 1

        lead = [s for s in white_squares if lead_row_lo <= s <= lead_row_hi]
        rest = [s for s in white_squares if s < lead_row_lo]

        lead_count = len(lead)
        assert lead_count >= 1

        # colex on the whole allowed band, then subtract the pure
        # non-lead combinations (the same difference that
        # men_combinations evaluates).
        allowed_lo = (dimension - 1 - white_man_rank) * row_width + 1
        allowed_hi = dimension * row_width
        allowed = list(range(allowed_lo, allowed_hi + 1))
        domain_index = {sq: i for i, sq in enumerate(allowed)}
        transformed = [domain_index[s] for s in white_squares]
        full_rank = colex_rank(transformed, n=len(allowed))

        # ranks that place nothing on the lead row
        non_lead_allowed = list(range(allowed_lo, lead_row_lo))
        non_lead_index = {sq: i for i, sq in enumerate(non_lead_allowed)}
        if all(s in non_lead_index for s in white_squares):
            non_lead_transformed = [non_lead_index[s] for s in white_squares]
            non_lead_rank = colex_rank(non_lead_transformed, n=len(non_lead_allowed))
        else:
            non_lead_rank = 0

        return full_rank - non_lead_rank

    if white_count == 0:
        # Symmetric to the white-only case.
        black_squares = sorted(position.bm)
        lead_row_lo = black_man_rank * row_width + 1
        lead_row_hi = lead_row_lo + row_width - 1

        allowed_lo = 1
        allowed_hi = (black_man_rank + 1) * row_width
        allowed = list(range(allowed_lo, allowed_hi + 1))
        domain_index = {sq: i for i, sq in enumerate(allowed)}
        transformed = [domain_index[s] for s in black_squares]
        full_rank = colex_rank(transformed, n=len(allowed))

        non_lead_allowed = list(range(allowed_lo, lead_row_lo))
        non_lead_index = {sq: i for i, sq in enumerate(non_lead_allowed)}
        if all(s in non_lead_index for s in black_squares):
            non_lead_transformed = [non_lead_index[s] for s in black_squares]
            non_lead_rank = colex_rank(non_lead_transformed, n=len(non_lead_allowed))
        else:
            non_lead_rank = 0

        return full_rank - non_lead_rank

    # ------------------------------------------------------------------
    # Zero-overlap case – product of two independent ranks
    # ------------------------------------------------------------------
    overlap = overlap_rows(black_man_rank, white_man_rank)
    if overlap == 0:
        black_part = rank_lead_men(
            state.Position(bm=position.bm, wm=(), bk=(), wk=()),
            black_man_rank,
            0,
        )
        white_part = rank_lead_men(
            state.Position(bm=(), wm=position.wm, bk=(), wk=()),
            0,
            white_man_rank,
        )
        white_ways = men_combinations(white_count, white_man_rank)
        return black_part * white_ways + white_part

    # ------------------------------------------------------------------
    # Single-row overlap – specialised decomposition
    # ------------------------------------------------------------------
    if overlap == 1:
        # The shared region is exactly one row; the counting formula
        # used in men_rank_combinations is recovered by a single loop
        # over black-lead count.
        black_lead_lo = black_man_rank * row_width + 1
        black_lead_hi = black_lead_lo + row_width - 1

        black_lead = [s for s in position.bm if black_lead_lo <= s <= black_lead_hi]
        black_rest = [s for s in position.bm if s < black_lead_lo]

        black_lead_count = len(black_lead)
        assert 1 <= black_lead_count <= row_width

        # Rank of the black-lead combination
        lead_domain = list(range(black_lead_lo, black_lead_hi + 1))
        lead_index = {sq: i for i, sq in enumerate(lead_domain)}
        lead_transformed = [lead_index[s] for s in black_lead]
        lead_rank = colex_rank(lead_transformed, n=row_width)

        # Rank of the remaining black men inside the non-lead black area
        non_lead_area = black_man_rank * row_width
        rest_domain = list(range(1, black_lead_lo))
        rest_index = {sq: i for i, sq in enumerate(rest_domain)}
        rest_transformed = [rest_index[s] for s in black_rest]
        rest_rank = colex_rank(rest_transformed, n=non_lead_area)

        # White men are ranked in the residual white domain after the
        # black-lead squares have been removed, again forcing the white
        # lead row.
        white_non_lead_area = white_man_rank * row_width
        white_domain = [
            s
            for s in range(
                (dimension - 1 - white_man_rank) * row_width + 1,
                dimension * row_width + 1,
            )
            if s not in set(black_lead)
        ]
        # Force at least one white on its own lead row.
        white_full = colex_rank(
            [white_domain.index(s) for s in sorted(position.wm)],
            n=len(white_domain),
        )
        white_non_lead_domain = [
            s
            for s in white_domain
            if s < (dimension - 1 - white_man_rank) * row_width + 1
        ]
        if all(s in white_non_lead_domain for s in position.wm):
            white_non_lead = colex_rank(
                [white_non_lead_domain.index(s) for s in sorted(position.wm)],
                n=len(white_non_lead_domain),
            )
        else:
            white_non_lead = 0
        white_rank_val = white_full - white_non_lead

        # Compose according to the summation order of the special case.
        total = 0
        for prev_lead in range(1, black_lead_count):
            total += (
                choose(row_width, prev_lead)
                * choose(non_lead_area, black_count - prev_lead)
                * (
                    choose(
                        white_non_lead_area + row_width - prev_lead,
                        white_count,
                    )
                    - choose(white_non_lead_area, white_count)
                )
            )

        # Add the contribution of the exact black-lead count
        ways_for_this_lead = choose(non_lead_area, black_count - black_lead_count)
        white_ways_for_this = choose(
            white_non_lead_area + row_width - black_lead_count,
            white_count,
        ) - choose(white_non_lead_area, white_count)
        total += (
            lead_rank * ways_for_this_lead * white_ways_for_this
            + rest_rank * white_ways_for_this
            + white_rank_val
        )
        return total

    # ------------------------------------------------------------------
    # General overlap – mirror the double loop of count_men_overlap
    # ------------------------------------------------------------------
    (
        black_lead_lo,
        black_lead_hi,
        pure_overlap_lo,
        pure_overlap_hi,
        white_lead_lo,
        white_lead_hi,
    ) = _region_bounds(black_man_rank, white_man_rank)

    # Extract the four sets that appear in the counting formula
    white_lead = [s for s in position.wm if white_lead_lo <= s <= white_lead_hi]
    leading_white = len(white_lead)
    assert 1 <= leading_white <= row_width

    obstruct_region = set(range(black_lead_lo, black_lead_hi + 1)) | set(
        range(pure_overlap_lo, pure_overlap_hi + 1) if pure_overlap_lo else []
    )
    obstruct_blacks = [s for s in position.bm if s in obstruct_region]
    obstruct = len(obstruct_blacks)
    assert obstruct >= 1

    remaining_black = [s for s in position.bm if s not in obstruct_region]
    remaining_white = [
        s for s in position.wm if not (white_lead_lo <= s <= white_lead_hi)
    ]

    # Capacities used by the counting routine
    overlap_size = overlap * row_width
    white_capacity = white_man_rank * row_width
    black_area = (dimension - white_man_rank) * row_width
    available_black = black_area - leading_white
    remaining_white_count = white_count - leading_white

    # ------------------------------------------------------------------
    # Accumulate the sizes of all preceding (leading_white, obstruct)
    # pairs, then add the mixed-radix rank inside the current pair.
    # ------------------------------------------------------------------
    total = 0

    max_leading_white = min(row_width, white_count)

    for prev_lead in range(1, leading_white):
        rem_w = white_count - prev_lead
        avail_b = black_area - prev_lead
        lo = max(1, black_count - avail_b)
        hi = min(
            black_count,
            white_capacity - rem_w,
            row_width + overlap_size,
        )
        for prev_obstruct in range(lo, hi + 1):
            total += (
                choose(row_width, prev_lead)
                * (
                    choose(row_width + overlap_size, prev_obstruct)
                    - choose(overlap_size, prev_obstruct)
                )
                * choose(avail_b, black_count - prev_obstruct)
                * choose(white_capacity - prev_obstruct, rem_w)
            )

    # Same leading_white, preceding obstruct values
    rem_w = remaining_white_count
    avail_b = available_black
    lo = max(1, black_count - avail_b)
    hi = min(
        black_count,
        white_capacity - rem_w,
        row_width + overlap_size,
    )

    for prev_obstruct in range(lo, obstruct):
        total += (
            choose(row_width, leading_white)
            * (
                choose(row_width + overlap_size, prev_obstruct)
                - choose(overlap_size, prev_obstruct)
            )
            * choose(avail_b, black_count - prev_obstruct)
            * choose(white_capacity - prev_obstruct, rem_w)
        )

    # ------------------------------------------------------------------
    # Rank inside the current (leading_white, obstruct) cell
    # ------------------------------------------------------------------
    # 1. colex rank of the white-lead combination
    white_lead_domain = list(range(white_lead_lo, white_lead_hi + 1))
    wl_index = {sq: i for i, sq in enumerate(white_lead_domain)}
    wl_transformed = [wl_index[s] for s in sorted(white_lead)]
    white_lead_rank = colex_rank(wl_transformed, n=row_width)

    # 2. colex rank of the obstruction combination
    #    (the subtraction that forces ≥1 on the black-lead row is already
    #    guaranteed by the position; we rank among all C(W+M, obstruct)
    #    combinations and rely on the global offset having skipped the
    #    illegal ones).
    obstruct_domain = sorted(obstruct_region)
    obs_index = {sq: i for i, sq in enumerate(obstruct_domain)}
    obs_transformed = [obs_index[s] for s in sorted(obstruct_blacks)]
    obstruct_rank = colex_rank(obs_transformed, n=len(obstruct_domain))

    # 3. residual black men
    residual_black_domain = [
        s
        for s in range(1, dimension * row_width + 1)
        if s not in obstruct_region
        and s < white_lead_lo  # stay inside the black-side area
    ][
        :available_black
    ]  # exact capacity
    # safer construction matching the capacity arithmetic
    residual_black_domain = list(range(1, black_lead_lo)) + [
        s for s in range(black_lead_hi + 1, pure_overlap_lo) if pure_overlap_lo
    ]
    # The precise domain used by the counting formula is the black-side
    # non-overlap area after removal of the white-lead squares.
    # For ranking we only need a stable colex order of size `available_black`.
    rb_domain = list(range(1, available_black + 1))  # abstract indices
    # Map actual squares onto 0..available_black-1 by sorted order of the
    # legal residual squares.
    legal_residual = sorted(s for s in position.bm if s not in obstruct_region)
    # Because the counting formula only cares about cardinality, any
    # fixed bijection works provided unrank uses the identical order.
    # We adopt the natural numeric order of the squares that fall inside
    # the capacity region.
    capacity_squares = []
    for r in range(dimension):
        if r == black_man_rank:
            continue  # lead already counted in obstruct
        if pure_overlap_lo and pure_overlap_lo <= r * row_width + 1 <= pure_overlap_hi:
            continue
        capacity_squares.extend(range(r * row_width + 1, (r + 1) * row_width + 1))
    capacity_squares = capacity_squares[:available_black]
    cap_index = {sq: i for i, sq in enumerate(capacity_squares)}
    rb_transformed = [cap_index[s] for s in legal_residual]
    residual_black_rank = colex_rank(rb_transformed, n=available_black)

    # 4. residual white men
    residual_white_capacity = white_capacity - obstruct
    legal_residual_white = sorted(remaining_white)
    # Abstract domain of size residual_white_capacity
    rw_domain_size = residual_white_capacity
    # Map onto the concrete squares that remain after obstruction
    white_side_squares = list(
        range(
            (dimension - white_man_rank) * row_width + 1,
            dimension * row_width + 1,
        )
    )
    # remove the obstructing black squares and the white-lead squares
    free_white = [
        s
        for s in white_side_squares
        if s not in obstruct_region and not (white_lead_lo <= s <= white_lead_hi)
    ][:rw_domain_size]
    free_index = {sq: i for i, sq in enumerate(free_white)}
    rw_transformed = [free_index[s] for s in legal_residual_white]
    residual_white_rank = colex_rank(rw_transformed, n=rw_domain_size)

    # Mixed-radix composition inside the cell
    # order: white_lead  →  obstruct  →  residual_black  →  residual_white
    ways_obstruct = choose(row_width + overlap_size, obstruct) - choose(
        overlap_size, obstruct
    )
    ways_residual_black = choose(available_black, black_count - obstruct)
    ways_residual_white = choose(residual_white_capacity, remaining_white_count)

    cell_rank = (
        white_lead_rank * ways_obstruct * ways_residual_black * ways_residual_white
        + obstruct_rank * ways_residual_black * ways_residual_white
        + residual_black_rank * ways_residual_white
        + residual_white_rank
    )

    total += choose(row_width, leading_white) * cell_rank
    return total


def unrank_lead_men(
    material: state.Material,
    index: int,
    black_man_rank: int,
    white_man_rank: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """
    Inverse of :func:`rank_lead_men`.

    Reconstructs the unique pair ``(black_men, white_men)`` whose
    rank under the given advancement limits equals ``index``.

    The algorithm mirrors the hierarchical decomposition used by the
    ranking function and by :func:`count_men_overlap`.
    """
    black_count = material.bm
    white_count = material.wm

    if black_count == 0 and white_count == 0:
        return (), ()

    row_width = layout.SQ_PER_ROW
    dimension = layout.DIMENSION

    # ------------------------------------------------------------------
    # Single-side cases
    # ------------------------------------------------------------------
    if black_count == 0:
        # Unrank white men inside the white-allowed band,
        # forcing the lead row.
        allowed_lo = (dimension - 1 - white_man_rank) * row_width + 1
        allowed_hi = dimension * row_width
        allowed = list(range(allowed_lo, allowed_hi + 1))
        full_ways = choose(len(allowed), white_count)
        non_lead_allowed = list(
            range(allowed_lo, (dimension - 1 - white_man_rank) * row_width + 1)
        )
        non_lead_ways = choose(len(non_lead_allowed), white_count)

        # The legal ranks are [non_lead_ways, full_ways).
        # Map the supplied index onto that interval.
        assert 0 <= index < full_ways - non_lead_ways
        target = index + non_lead_ways

        transformed = colex_unrank(target, white_count, len(allowed))
        white_men = tuple(sorted(allowed[i] for i in transformed))
        return (), white_men

    if white_count == 0:
        allowed_lo = 1
        allowed_hi = (black_man_rank + 1) * row_width
        allowed = list(range(allowed_lo, allowed_hi + 1))
        full_ways = choose(len(allowed), black_count)
        non_lead_allowed = list(range(allowed_lo, black_man_rank * row_width + 1))
        non_lead_ways = choose(len(non_lead_allowed), black_count)

        assert 0 <= index < full_ways - non_lead_ways
        target = index + non_lead_ways

        transformed = colex_unrank(target, black_count, len(allowed))
        black_men = tuple(sorted(allowed[i] for i in transformed))
        return black_men, ()

    # ------------------------------------------------------------------
    # Zero-overlap case
    # ------------------------------------------------------------------
    overlap = overlap_rows(black_man_rank, white_man_rank)
    if overlap == 0:
        white_ways = men_combinations(white_count, white_man_rank)
        black_index = index // white_ways
        white_index = index % white_ways

        black_men, _ = unrank_lead_men(
            state.Material(bm=black_count, wm=0, bk=0, wk=0),
            black_index,
            black_man_rank,
            0,
        )
        _, white_men = unrank_lead_men(
            state.Material(bm=0, wm=white_count, bk=0, wk=0),
            white_index,
            0,
            white_man_rank,
        )
        return black_men, white_men

    # ------------------------------------------------------------------
    # Single-row overlap (special case)
    # ------------------------------------------------------------------
    if overlap == 1:
        non_lead_area = black_man_rank * row_width
        white_non_lead_area = white_man_rank * row_width

        remainder = index
        for black_lead_count in range(1, min(black_count, row_width) + 1):
            ways = (
                choose(row_width, black_lead_count)
                * choose(non_lead_area, black_count - black_lead_count)
                * (
                    choose(
                        white_non_lead_area + row_width - black_lead_count,
                        white_count,
                    )
                    - choose(white_non_lead_area, white_count)
                )
            )
            if remainder < ways:
                # Decode inside this black-lead count
                lead_ways = choose(row_width, black_lead_count)
                rest_ways = choose(non_lead_area, black_count - black_lead_count)
                white_ways = choose(
                    white_non_lead_area + row_width - black_lead_count,
                    white_count,
                ) - choose(white_non_lead_area, white_count)

                lead_rank = remainder // (rest_ways * white_ways)
                remainder %= rest_ways * white_ways
                rest_rank = remainder // white_ways
                white_rank_val = remainder % white_ways

                # Unrank black lead
                lead_domain = list(
                    range(
                        black_man_rank * row_width + 1,
                        (black_man_rank + 1) * row_width + 1,
                    )
                )
                lead_idx = colex_unrank(lead_rank, black_lead_count, row_width)
                black_lead = [lead_domain[i] for i in lead_idx]

                # Unrank residual black
                rest_domain = list(range(1, black_man_rank * row_width + 1))
                rest_idx = colex_unrank(
                    rest_rank, black_count - black_lead_count, non_lead_area
                )
                black_rest = [rest_domain[i] for i in rest_idx]

                black_men = tuple(sorted(black_lead + black_rest))

                # Unrank white (force lead)
                white_domain = [
                    s
                    for s in range(
                        (dimension - 1 - white_man_rank) * row_width + 1,
                        dimension * row_width + 1,
                    )
                    if s not in set(black_lead)
                ]
                non_lead_w = [
                    s
                    for s in white_domain
                    if s < (dimension - 1 - white_man_rank) * row_width + 1
                ]
                non_lead_ways_w = choose(len(non_lead_w), white_count)
                target = white_rank_val + non_lead_ways_w
                w_idx = colex_unrank(target, white_count, len(white_domain))
                white_men = tuple(sorted(white_domain[i] for i in w_idx))

                return black_men, white_men

            remainder -= ways

        raise IndexError("index out of range for single-row overlap")

    # ------------------------------------------------------------------
    # General overlap
    # ------------------------------------------------------------------
    overlap_size = overlap * row_width
    white_capacity = white_man_rank * row_width
    black_area = (dimension - white_man_rank) * row_width

    (
        black_lead_lo,
        black_lead_hi,
        pure_overlap_lo,
        pure_overlap_hi,
        white_lead_lo,
        white_lead_hi,
    ) = _region_bounds(black_man_rank, white_man_rank)

    remainder = index
    max_leading_white = min(row_width, white_count)

    for leading_white in range(1, max_leading_white + 1):
        remaining_white = white_count - leading_white
        available_black = black_area - leading_white

        min_obstruct = max(1, black_count - available_black)
        max_obstruct = min(
            black_count,
            white_capacity - remaining_white,
            row_width + overlap_size,
        )

        for obstruct in range(min_obstruct, max_obstruct + 1):
            ways = (
                choose(row_width, leading_white)
                * (
                    choose(row_width + overlap_size, obstruct)
                    - choose(overlap_size, obstruct)
                )
                * choose(available_black, black_count - obstruct)
                * choose(white_capacity - obstruct, remaining_white)
            )

            if remainder < ways:
                # Decode the four colex ranks inside this cell
                cell_size = ways // choose(row_width, leading_white)
                lead_rank = remainder // cell_size
                remainder %= cell_size

                ways_obs = choose(row_width + overlap_size, obstruct) - choose(
                    overlap_size, obstruct
                )
                ways_rb = choose(available_black, black_count - obstruct)
                ways_rw = choose(white_capacity - obstruct, remaining_white)

                obs_rank = remainder // (ways_rb * ways_rw)
                remainder %= ways_rb * ways_rw
                rb_rank = remainder // ways_rw
                rw_rank = remainder % ways_rw

                # Unrank white lead
                white_lead_domain = list(range(white_lead_lo, white_lead_hi + 1))
                wl_idx = colex_unrank(lead_rank, leading_white, row_width)
                white_lead = [white_lead_domain[i] for i in wl_idx]

                # Unrank obstruction (among the legal combinations that
                # already satisfy the ≥1 black-lead constraint)
                obstruct_domain = sorted(
                    set(range(black_lead_lo, black_lead_hi + 1))
                    | set(
                        range(pure_overlap_lo, pure_overlap_hi + 1)
                        if pure_overlap_lo
                        else []
                    )
                )
                # The rank we stored is among the *all* C(W+M,k)
                # combinations; we must skip those with zero black-lead
                # men.  Because the counting formula already subtracted
                # them, the stored obs_rank is the rank among the legal
                # subset.  We therefore generate the legal combinations
                # on the fly by walking colex until we have seen
                # obs_rank legal ones.
                legal_count = 0
                target_combo = None
                for combo_rank in range(choose(len(obstruct_domain), obstruct)):
                    combo = colex_unrank(combo_rank, obstruct, len(obstruct_domain))
                    squares = [obstruct_domain[i] for i in combo]
                    if any(black_lead_lo <= s <= black_lead_hi for s in squares):
                        if legal_count == obs_rank:
                            target_combo = squares
                            break
                        legal_count += 1
                assert target_combo is not None
                obstruct_blacks = target_combo

                # Unrank residual black
                capacity_squares = []
                for r in range(dimension):
                    if r == black_man_rank:
                        continue
                    if (
                        pure_overlap_lo
                        and pure_overlap_lo <= r * row_width + 1 <= pure_overlap_hi
                    ):
                        continue
                    capacity_squares.extend(
                        range(r * row_width + 1, (r + 1) * row_width + 1)
                    )
                capacity_squares = capacity_squares[:available_black]
                rb_idx = colex_unrank(rb_rank, black_count - obstruct, available_black)
                residual_black = [capacity_squares[i] for i in rb_idx]

                black_men = tuple(sorted(obstruct_blacks + residual_black))

                # Unrank residual white
                white_side = list(
                    range(
                        (dimension - white_man_rank) * row_width + 1,
                        dimension * row_width + 1,
                    )
                )
                free_white = [
                    s
                    for s in white_side
                    if s not in set(obstruct_blacks)
                    and not (white_lead_lo <= s <= white_lead_hi)
                ][: white_capacity - obstruct]
                rw_idx = colex_unrank(
                    rw_rank, remaining_white, white_capacity - obstruct
                )
                residual_white = [free_white[i] for i in rw_idx]

                white_men = tuple(sorted(white_lead + residual_white))
                return black_men, white_men

            remainder -= ways

    raise IndexError("index out of range for general overlap")
```
