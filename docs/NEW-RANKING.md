# Ranking

```Python
def _comb_rank(values: tuple[int, ...], domain: tuple[int, ...]) -> int:
    """Colexicographic rank of a combination drawn from domain."""
    if not values:
        return 0

    index = {sq: i for i, sq in enumerate(domain)}
    return colex_rank(
        [index[sq] for sq in sorted(values)],
        n=len(domain),
    )


def _comb_unrank(
    rank: int,
    count: int,
    domain: tuple[int, ...],
) -> tuple[int, ...]:
    """Unrank a colexicographic combination from domain."""
    if count == 0:
        return ()

    idx = colex_unrank(rank, count, len(domain))
    return tuple(sorted(domain[i] for i in idx))


def _rank_general_overlap(
    position: state.Position,
    black_man_rank: int,
    white_man_rank: int,
) -> int:
    """
    Rank a men-only position in the general-overlap region.

    The ranking order is:

        1. number and placement of white men on the white leading row
        2. black obstruction placement
        3. residual black placement
        4. residual white placement

    The ordering is identical to the ordering used by
    ``count_men_overlap``.
    """
    W = layout.SQ_PER_ROW
    H = layout.DIMENSION
    bm = position.material.bm
    wm = position.material.wm

    overlap = overlap_rows(black_man_rank, white_man_rank) * W
    white_capacity = white_man_rank * W
    black_capacity = (H - white_man_rank) * W

    black_lead_lo, black_lead_hi = _lead_row_bounds(
        black_man_rank,
        from_black=True,
    )
    white_lead_lo, white_lead_hi = _lead_row_bounds(
        white_man_rank,
        from_black=False,
    )

    white_lead_domain = tuple(
        range(white_lead_lo, white_lead_hi + 1)
    )

    white_lead = tuple(
        sorted(
            s for s in position.wm
            if white_lead_lo <= s <= white_lead_hi
        )
    )
    leading_white = len(white_lead)

    # ------------------------------------------------------------------
    # Obstruction domain
    # ------------------------------------------------------------------

    obstruction_domain = tuple(
        _obstruction_domain(
            black_man_rank,
            white_man_rank,
        )
    )

    obstruction = tuple(
        sorted(
            s for s in position.bm
            if s in obstruction_domain
        )
    )
    obstruct = len(obstruction)

    remaining_white = tuple(
        sorted(
            s for s in position.wm
            if s not in white_lead
        )
    )

    residual_black = tuple(
        sorted(
            s for s in position.bm
            if s not in obstruction
        )
    )

    # ------------------------------------------------------------------
    # Rank preceding leading-white / obstruction cells.
    # ------------------------------------------------------------------

    total = 0

    for prev_lw in range(1, leading_white):
        rem_w = wm - prev_lw
        avail_black = black_capacity - prev_lw

        lo = max(1, bm - avail_black)
        hi = min(
            bm,
            white_capacity - rem_w,
            W + overlap,
        )

        for prev_ob in range(lo, hi + 1):
            ways_ob = (
                choose(W + overlap, prev_ob)
                - choose(overlap, prev_ob)
            )

            ways_rb = choose(
                avail_black,
                bm - prev_ob,
            )

            ways_rw = choose(
                white_capacity - prev_ob,
                rem_w,
            )

            total += (
                choose(W, prev_lw)
                * ways_ob
                * ways_rb
                * ways_rw
            )

    # ------------------------------------------------------------------
    # Rank obstruction cells preceding the current obstruction.
    # ------------------------------------------------------------------

    avail_black = black_capacity - leading_white
    rem_w = wm - leading_white

    lo = max(1, bm - avail_black)

    for prev_ob in range(lo, obstruct):
        ways_ob = (
            choose(W + overlap, prev_ob)
            - choose(overlap, prev_ob)
        )

        ways_rb = choose(
            avail_black,
            bm - prev_ob,
        )

        ways_rw = choose(
            white_capacity - prev_ob,
            rem_w,
        )

        total += (
            choose(W, leading_white)
            * ways_ob
            * ways_rb
            * ways_rw
        )

    # ------------------------------------------------------------------
    # Rank inside the current leading-white cell.
    # ------------------------------------------------------------------

    white_lead_rank = _comb_rank(
        white_lead,
        white_lead_domain,
    )

    ways_ob = (
        choose(W + overlap, obstruct)
        - choose(overlap, obstruct)
    )

    ways_rb = choose(
        avail_black,
        bm - obstruct,
    )

    ways_rw = choose(
        white_capacity - obstruct,
        rem_w,
    )

    total += (
        white_lead_rank
        * ways_ob
        * ways_rb
        * ways_rw
    )

    # ------------------------------------------------------------------
    # Obstruction rank.
    #
    # Only combinations containing at least one square from the
    # black leading row are legal.
    # ------------------------------------------------------------------

    legal_rank = 0

    for r in range(
        choose(len(obstruction_domain), obstruct)
    ):
        candidate = _comb_unrank(
            r,
            obstruct,
            obstruction_domain,
        )

        if not any(
            black_lead_lo <= sq <= black_lead_hi
            for sq in candidate
        ):
            continue

        if candidate == obstruction:
            break

        legal_rank += 1

    total += legal_rank * ways_rb * ways_rw

    # ------------------------------------------------------------------
    # Residual black rank.
    #
    # Construct the domain from the actual black-side geometry and
    # remove the selected obstruction and white-leading squares.
    # ------------------------------------------------------------------

    black_domain = tuple(
        s
        for s in range(1, (H - white_man_rank) * W + 1)
        if s not in obstruction
        and s not in white_lead
    )

    residual_black_rank = _comb_rank(
        residual_black,
        black_domain,
    )

    total += residual_black_rank * ways_rw

    # ------------------------------------------------------------------
    # Residual white rank.
    # ------------------------------------------------------------------

    white_domain = tuple(
        s
        for s in range(
            max(1, (H - 1 - white_man_rank) * W + 1),
            layout.SQ_COUNT + 1,
        )
        if s not in white_lead
        and s not in obstruction
    )

    residual_white_rank = _comb_rank(
        remaining_white,
        white_domain,
    )

    total += residual_white_rank

    return total
```
