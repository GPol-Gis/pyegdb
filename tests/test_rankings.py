"""
Public-API tests for size / rank / unrank.

Only the three exported functions are exercised.  The board layout is
forced to ENGLISH and re-initialised before every test.
"""

from __future__ import annotations

import pytest

from pyegdb import layout, state
from pyegdb.subdb import rank, size, unrank

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def english_board():
    """Re-initialise the ENGLISH layout before every test."""
    layout.initialize(layout=layout.BoardLayout.ENGLISH)
    yield
    # optional: layout.reset() if the library provides it


def make_material(bm: int = 0, wm: int = 0, bk: int = 0, wk: int = 0) -> state.Material:
    return state.Material(bm=bm, wm=wm, bk=bk, wk=wk)


# ---------------------------------------------------------------------------
# size
# ---------------------------------------------------------------------------


class TestSize:
    def test_empty(self):
        m = make_material()
        assert size(m) >= 1

    @pytest.mark.parametrize(
        "bm,wm,bk,wk",
        [
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (2, 1, 0, 0),
            (0, 0, 1, 1),
            (1, 1, 1, 0),
            (3, 2, 0, 1),
        ],
    )
    def test_positive(self, bm, wm, bk, wk):
        assert size(make_material(bm, wm, bk, wk)) > 0

    @pytest.mark.parametrize(
        "bm,wm,br,wr",
        [
            (0, 0, 0, 0),
            (2, 0, 1, 0),
            (0, 3, 0, 2),
            (2, 2, 1, 1),
            (2, 2, 3, 3),
            (3, 2, 4, 4),
            (1, 1, 2, 3),
        ],
    )
    def test_constrained_positive(self, bm, wm, br, wr):
        m = make_material(bm, wm)
        s = size(m, black_man_rank=br, white_man_rank=wr)
        assert s >= 0

    def test_constrained_vs_unconstrained(self):
        """Constrained size never exceeds the unconstrained size."""
        m = make_material(2, 2)
        unconstrained = size(m)
        for br in range(layout.DIMENSION):
            for wr in range(layout.DIMENSION):
                constrained = size(m, black_man_rank=br, white_man_rank=wr)
                assert 0 <= constrained <= unconstrained


# ---------------------------------------------------------------------------
# rank / unrank  (unconstrained)
# ---------------------------------------------------------------------------


class TestRankUnrankUnconstrained:
    @pytest.mark.parametrize(
        "bm,wm,bk,wk",
        [
            (0, 0, 0, 0),
            (1, 0, 0, 0),
            (0, 1, 0, 0),
            (2, 1, 0, 0),
            (0, 0, 1, 1),
            (1, 1, 1, 0),
            (3, 2, 0, 1),
        ],
    )
    def test_round_trip(self, bm, wm, bk, wk):
        material = make_material(bm, wm, bk, wk)
        space = size(material)
        step = max(1, space // 40)
        indices = list(range(0, space, step))
        if space and (space - 1) not in indices:
            indices.append(space - 1)

        for idx in indices:
            pos = unrank(idx, material)
            assert pos.material == material
            recovered = rank(pos)
            assert recovered == idx, (
                f"round-trip failed: material={material} idx={idx} "
                f"-> {pos} -> rank={recovered}"
            )

    def test_rank_in_range(self):
        material = make_material(2, 1)
        space = size(material)
        for idx in range(min(space, 30)):
            pos = unrank(idx, material)
            r = rank(pos)
            assert 0 <= r < space

    def test_unrank_out_of_range(self):
        material = make_material(1, 1)
        space = size(material)
        with pytest.raises((IndexError, ValueError)):
            unrank(space, material)

    def test_empty(self):
        material = make_material()
        pos = unrank(0, material)
        assert pos.bm == () and pos.wm == () and pos.bk == () and pos.wk == ()
        assert rank(pos) == 0

    def test_dense_unique(self):
        material = make_material(2, 1)
        space = size(material)
        seen = set()
        for idx in range(space):
            pos = unrank(idx, material)
            r = rank(pos)
            assert r not in seen
            seen.add(r)
        assert seen == set(range(space))


# ---------------------------------------------------------------------------
# rank / unrank  (lead-men / constrained)
# ---------------------------------------------------------------------------


class TestRankUnrankLeadMen:
    """
    Exercises the constrained path.

    rank(..., constrain_by_lead_men=True) together with
    unrank(..., black_man_rank=..., white_man_rank=...) must form a
    bijection onto [0, size(..., black_man_rank=..., white_man_rank=...)).
    """

    @pytest.mark.parametrize(
        "bm,wm,bk,wk,br,wr",
        [
            (0, 0, 0, 0, 0, 0),
            (1, 0, 0, 0, 1, 0),
            (0, 1, 0, 0, 0, 1),
            (2, 1, 0, 0, 2, 2),
            (1, 1, 1, 0, 3, 3),
            (2, 2, 0, 1, 4, 4),
            (3, 1, 1, 1, 5, 3),
            (2, 2, 0, 0, 1, 1),  # possible zero-overlap
            (2, 2, 0, 0, 3, 3),  # single-row or general overlap
        ],
    )
    def test_round_trip(self, bm, wm, bk, wk, br, wr):
        material = make_material(bm, wm, bk, wk)
        space = size(material, black_man_rank=br, white_man_rank=wr)
        if space == 0:
            pytest.skip("empty configuration space")

        step = max(1, space // 20)
        indices = list(range(0, space, step))
        if space - 1 not in indices:
            indices.append(space - 1)

        for idx in indices:
            pos = unrank(
                idx,
                material,
                black_man_rank=br,
                white_man_rank=wr,
            )
            assert pos.material == material

            recovered = rank(pos, constrain_by_lead_men=True)
            assert recovered == idx, (
                f"lead-men round-trip failed: material={material} "
                f"ranks=({br},{wr}) idx={idx} -> {pos} -> rank={recovered}"
            )

    @pytest.mark.parametrize(
        "bm,wm,br,wr",
        [
            (1, 1, 0, 0),
            (2, 1, 2, 2),
            (3, 2, 4, 3),
            (0, 2, 0, 1),
            (2, 0, 1, 0),
        ],
    )
    def test_rank_in_range(self, bm, wm, br, wr):
        material = make_material(bm, wm)
        space = size(material, black_man_rank=br, white_man_rank=wr)
        for idx in range(min(space, 20)):
            pos = unrank(idx, material, black_man_rank=br, white_man_rank=wr)
            r = rank(pos, constrain_by_lead_men=True)
            assert 0 <= r < space

    def test_unrank_out_of_range(self):
        material = make_material(2, 2)
        space = size(material, black_man_rank=3, white_man_rank=3)
        with pytest.raises((IndexError, ValueError)):
            unrank(space, material, black_man_rank=3, white_man_rank=3)

    def test_empty_constrained(self):
        material = make_material()
        assert size(material, black_man_rank=0, white_man_rank=0) >= 1
        pos = unrank(0, material, black_man_rank=0, white_man_rank=0)
        assert pos.bm == () and pos.wm == ()
        assert rank(pos, constrain_by_lead_men=True) == 0

    def test_dense_unique(self):
        material = make_material(2, 1)
        br, wr = 3, 2
        space = size(material, black_man_rank=br, white_man_rank=wr)
        seen = set()
        for idx in range(space):
            pos = unrank(idx, material, black_man_rank=br, white_man_rank=wr)
            r = rank(pos, constrain_by_lead_men=True)
            assert r not in seen
            seen.add(r)
        assert len(seen) == space

    def test_kings_do_not_collide(self):
        material = make_material(1, 1, 1, 1)
        br, wr = 3, 3
        space = size(material, black_man_rank=br, white_man_rank=wr)
        for idx in [0, space // 3, space // 2, max(0, space - 1)]:
            if idx >= space:
                continue
            pos = unrank(idx, material, black_man_rank=br, white_man_rank=wr)
            occupied = set(pos.bm) | set(pos.wm)
            if pos.bk:
                assert pos.bk[0] not in occupied
            if pos.wk:
                assert pos.wk[0] not in occupied


# ---------------------------------------------------------------------------
# Cross-check: constrain_by_lead_men=False ignores rank kwargs
# ---------------------------------------------------------------------------


class TestDispatch:
    def test_unconstrained_path_ignores_ranks(self):
        """When constrain_by_lead_men is false, rank uses the ordinary material space."""
        material = make_material(2, 1)
        pos = unrank(0, material)  # unconstrained unrank
        r1 = rank(pos)  # default
        r2 = rank(pos, constrain_by_lead_men=False)
        assert r1 == r2
        # The constrained size may be smaller; the unconstrained rank
        # is still well-defined and must lie in the unconstrained space.
        assert 0 <= r1 < size(material)
