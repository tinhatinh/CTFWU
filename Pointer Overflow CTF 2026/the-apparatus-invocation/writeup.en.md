# The Apparatus, Invocation - Misc

**Points:** 100 · **Wave:** 1 · **Flag:** `POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}`

**Artifact:** no file to download; the board is generated per team and sits right on the page
`/challenges/the-apparatus-invocation/`. Team 612's initial state is saved in `files/board.txt`.

## Challenge

Forty-nine candles arranged in a 7x7 grid. Clicking a candle puts it out and perturbs the four candles adjacent
to it along the vertical and horizontal axes. To invoke the apparatus's name you must get the whole board dark.
The page states that click order does not matter, only the set of clicks carries meaning, and Reset returns the board to exactly its initial state.

## Initial Analysis

Read the DOM to get two things: the board state and how the page verifies a solve.

```html
<div id="board" class="board" role="grid" aria-label="Invocation board">
  <button type="button" class="cell" data-r="0" data-c="0" role="gridcell"
          aria-label="Candle at row 1 column 1" aria-pressed="false"></button>
  ...
```

In the inline script (4.3 KB) there are three details that decide how the challenge must be done:

- The flag is **not** in the HTML. `const presetFlag = ""` and `const alreadySolved = false`, while on
  a win the page calls `fetch(window.location.pathname + 'complete', {body: JSON.stringify({clicks: presses})})`
  and then assigns `$flagTxt.textContent = d.flag`. That means the server replays the click list on the
  team's board and generates the flag itself; there is no shortcut from the client.
- `presses` is an array of `{r, c}` pushed on every click, so it is enough to trigger the page's own
  handler correctly; there is no need to recompute the state yourself.
- The board is rendered with `classList.toggle('lit', on)` alongside `aria-pressed`, so reading
  `aria-pressed` in DOM order (row-major) yields exactly the 7x7 matrix.

The state that was read (`1` is a lit candle):

```text
0000000
0000110
1100001
1001011
1000110
1111010
0110110
```

## Exploit Chain

**Step 1 - Model it.** Because every click is a constant addition over GF(2) and the clicks commute, the
problem is `A x = b`: row `i` corresponds to cell `i`, `A[i][j] = 1` if clicking `j` flips cell `i` (that is
`j = i` or `j` adjacent to `i`), and `b[i]` is the initial state of cell `i` (it must be flipped an odd number of times).

**Step 2 - Solve the system.** Gaussian elimination on a 49x50 matrix. The rank of `A` is 49, there are
no free variables, so the solution is unique - every board is solvable and there is no chance of picking
the wrong solution. For team 612 the result is 14 cells (0-indexed):

```text
(2,4) (2,5) (3,0) (3,1) (3,3) (4,0) (4,6) (5,0) (5,3) (5,4) (5,6) (6,0) (6,3) (6,5)
```

**Step 3 - Verify locally.** Replay the 14 clicks on the initial board using the script's own
`neighbors()` function, confirming that every cell returns to 0 before touching the page.

**Step 4 - Play on the page.** Fire real click events at exactly the 14 buttons so that the page's
handler records `presses` and calls the endpoint itself:

```js
() => { const P=[[2,4],[2,5],[3,0],[3,1],[3,3],[4,0],[4,6],[5,0],[5,3],[5,4],[5,6],[6,0],[6,3],[6,5]];
  for (const [r,c] of P) document.querySelector(`#board .cell[data-r="${r}"][data-c="${c}"]`).click(); }
```

`press-count` goes to 14, `#flag-box` appears and `#flag-text` receives the flag from the server.

## Flag

```text
POCTF{3.612.H5VA2OHFE333SO62.EAIOF76YB2L4XMZTFSV4CPOEOX}
```

Matches the template `POCTF{<cid>.<team_id>.<nonce>.<sig26>}` with cid 3, team 612, a 16-character
nonce, and a 26-character base32 sig.

## Reproduce

```bash
cd the-apparatus-invocation
python exploit.py
```

The script prints the 14 cells to click again from `files/board.txt` together with the JS snippet to paste into the
page. To do it with another team's board, replace `files/board.txt` with the pattern read from the DOM using the command in `de.md`.
