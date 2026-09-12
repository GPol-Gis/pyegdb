# Lexicographical Ranking

```Python
from math import comb
from typing import Sequence

def revlex_rank(values: Sequence[int], n: int) -> int:
    """Return the reverse lexicographic rank of a combination in 0..n-1."""
    if any(v < 0 or v >= n for v in values):
        raise ValueError(f"coordinate out of range [0, {n}): {values}")

    values = sorted(values)  # ensure increasing order
    k = len(values)
    return sum(comb(n - 1 - v, k - i) for i, v in enumerate(values))


def revlex_unrank(rank: int, k: int, n: int) -> list[int]:
    """Return the k-combination of 0..n-1 at given revlex rank."""
    values = []
    r = rank
    for i in range(k):
        for v in range(n):
            c = comb(n - 1 - v, k - i)
            if c <= r:
                r -= c
            else:
                values.append(v)
                break
    return values


def revlex_rank_bitboard(bb: int, n: int) -> int:
    """Revlex rank of bitboard subset in 0..n-1."""
    rank = 0
    k = bb.bit_count()
    i = 0
    for v in range(n):
        if (bb >> v) & 1:  # bit set
            rank += comb(n - 1 - v, k - i)
            i += 1
    return rank

def revlex_unrank_bitboard(rank: int, k: int, n: int) -> int:
    """Return bitboard of k-subset at given revlex rank."""
    bb = 0
    r = rank
    chosen = 0
    for v in range(n):
        c = comb(n - 1 - v, k - chosen)
        if c <= r:
            r -= c
        else:
            bb |= (1 << v)
            chosen += 1
            if chosen == k:
                break
    return bb
```
