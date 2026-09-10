# Counting Men Placements by Leading Rank in Checkers / Draughts

## Overview

The function `count_man(bm, wm, bl, wl)` returns the number of ways to place  

- `bm` black men,  
- `wm` white men  

on an \(H \times R\) board (only the dark squares) such that  

- the highest rank occupied by any black man is exactly `bl`,  
- the highest rank occupied by any white man is exactly `wl`.  

Ranks are numbered \(0 \dots H-2\) from each player’s own back rank; rank \(H-1\) is the promotion rank and therefore never contains a man.

After the men have been placed, the remaining squares may be filled arbitrarily with kings.  The product of the two quantities yields the exact number of positions for a given material signature and leading-rank pair.  Summing over all admissible signatures recovers the well-known totals used by Chinook and later end-game database generators.

## Board Geometry

- \(H\) = number of ranks (8 for English draughts, 10 for international, \ldots)  
- \(R\) = number of playable squares per rank (4 on 8×8, 5 on 10×10, \ldots)  
- \(N = H\cdot R\)  

Black’s ranks increase toward White’s promotion rank; White’s ranks increase in the opposite direction.  Consequently the two leading ranks may be

- completely disjoint,  
- adjacent, or  
- overlapping.

The algorithm partitions the board according to the relative positions of the two leading ranks.

## Case Analysis

### 1. Trivial cases

- \(bm = wm = 0\) → 1 (empty placement).  
- One side empty → ordinary “at-least-one-on-the-lead-rank” identity  

  \[
  \binom{(l+1)R}{m} - \binom{lR}{m}.
  \]

### 2. Disjoint leading ranks (`bl + wl < H-1`)

The two placement regions do not touch.  The result is simply the product of the two independent binomial differences.

### 3. Same leading rank (`h_o = 1`)

The single shared rank of \(R\) squares must contain at least one black man and at least one white man.  The double loop enumerates every admissible split \((i,j)\) of that rank and multiplies by the free placements of the remaining men on the exclusive lower ranks of each colour.

### 4. Overlapping leading ranks of height \(\ge 2\)

The board is divided into four regions:

| Region | Description                              | Size                  |
|--------|------------------------------------------|-----------------------|
| [1]    | Black’s lead rank \(L_b\)                | \(R\)                 |
| [2]    | White’s lead rank \(L_w\)                | \(R\)                 |
| [3]    | Pure middle overlap                      | \(M = (h_o-2)R\)      |
| [4]    | Black-exclusive zone                     | \(A = (H-1-wl)R\)     |

(The symmetric white-exclusive zone is handled implicitly by capacity constraints.)

The algorithm:

1. Places the obligatory men on the two lead ranks (\(i\ge 1\), \(j\ge 1\)).  
2. Distributes the remaining black men between the middle zone and the free squares of White’s lead rank, respecting the residual capacity for white men.  
3. Places the remaining white men on what is left.

All loop bounds are tight, guaranteeing that every legal configuration is counted exactly once and no illegal configuration is generated.

## Multiplication by Kings

Once the men occupy \(bm+wm\) squares, the remaining \(N-bm-wm\) squares may hold the kings in any way:

\[
\binom{N-bm-wm}{bk}\binom{N-bm-wm-bk}{wk}.
\]

## Complexity

All loops run over at most \(R\le 5\) values; the whole function is essentially constant time for any practical board size.  Binomial coefficients can be pre-computed or evaluated on the fly with a multiplicative formula; they fit comfortably in 64-bit integers for the ranges that appear in checkers (\(R\le 5\), total pieces \(\le 24\)).

## Correctness

The algorithm is the classic leading-rank decomposition employed by the Chinook project.  It produces exactly the numbers published in the Chinook “Positions by Leading Rank” tables and, when summed over all material and rank pairs, recovers the accepted total of \(500\,995\,484\,682\,338\,672\,639\) positions for English draughts.
