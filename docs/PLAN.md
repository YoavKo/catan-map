# Catan Map Generator — Plan

A small utility that makes a random, **reproducible** *Settlers of Catan* board from a seed, writes it as a short string, reads such a string back, and prints it in the console. First a command-line script; later images and a page on the OnlyGames site.

Status: **built: version 1.0.0** (15 October 2026), in this repository. The plan below was agreed in conversation the same day; the points where the finished tool differs from the plan are listed in section 11. The repository was created locally with `git init` and has not been pushed anywhere.

## 1. Scope (version 1)

- The **standard 19-tile board** with rows of **3, 4, 5, 4, 3** tiles and **9 ports**. Larger islands come later; the code keeps the row lengths and the piece counts as data, not hard-coded in many places.
- Pure Python, **no Flask or database dependency**, so it runs as a plain script and can be imported by the site later.

## 2. The board

### 2.1 Tiles (land)

Tile index 0–18, scanned **left to right, top to bottom**:

```
row 0:        0  1  2
row 1:      3  4  5  6
row 2:    7  8  9 10 11
row 3:     12 13 14 15
row 4:       16 17 18
```

- Tile letters: **W** wood, **O** ore, **C** clay, **S** sheep, **G** grain, **D** desert.
- Standard counts: 4 W, 4 S, 4 G, 3 O, 3 C, 1 D.
- The tiles fall into three zones:
  - **edge**: the **12** tiles that touch the sea: 0, 1, 2, 3, 6, 7, 11, 12, 15, 16, 17, 18.
  - **center**: tile **9**.
  - **ring**: the **6** tiles around the center: 4, 5, 8, 10, 13, 14.
  - **inner** = center + ring = the 7 tiles that do not touch the sea.

```
        e  e  e
      e  r  r  e
    e  r  C  r  e        e = edge   r = ring   C = center
      e  r  r  e
        e  e  e
```
- Two tiles are **neighbours** when they touch. With a doubled horizontal coordinate `x = 2·col − (row length − 1)`: same row and `|dx| = 2`, or adjacent rows and `|dx| = 1`.

### 2.2 Number tokens

- Symbols **`2 3 4 5 6 8 9 a b c`**, where `a` = 10, `b` = 11, `c` = 12 (there is no 7).
- Standard counts: one `2`, one `c`, and two each of `3 4 5 6 8 9 a b`: 18 tokens, one per tile except the desert.
- Tokens follow the tile scan order, **skipping the desert**.
- Tile letters are uppercase and token letters are lowercase, so `C` (clay) and `c` (12) never clash.

### 2.3 Ports (the sea ring)

The island is surrounded by a ring of **18 sea tiles**, numbered **0–17 clockwise from the top-left corner**:

```
0–3    top row, left to right (4 tiles)
4–8    right side, top to bottom (5 tiles)
9–12   bottom row, right to left (4 tiles)
13–17  left side, bottom to top (5 tiles)
```

Which island tiles each sea tile touches, in clockwise order:

| ring | touches | ring | touches | ring | touches |
|---|---|---|---|---|---|
| 0 | 0 | 6 | 11 | 12 | 16 |
| 1 | 0, 1 | 7 | 11, 15 | 13 | 16, 12 |
| 2 | 1, 2 | 8 | 15, 18 | 14 | 12, 7 |
| 3 | 2 | 9 | 18 | 15 | 7 |
| 4 | 2, 6 | 10 | 18, 17 | 16 | 7, 3 |
| 5 | 6, 11 | 11 | 17, 16 | 17 | 3, 0 |

- **Corner** sea tiles (0, 3, 6, 9, 12, 15) touch one island tile, so a port there has **one** way to attach. The other 12 touch two island tiles, so a port there has **two** legal orientations.
- A port attaches to the **edge shared with one island tile**: **backward** = the first tile in the list above (the earlier one in the clockwise scan), **forward** = the second.
- **A port never attaches to the desert** (a rule added after the first version, see section 11).
- **9 ports** sit on every second sea tile, with empty water between them: **4 × 3:1** and **5 × 2:1** (one per resource).
- Without the shift, port *k* (1–9) is on ring tile `2(k−1)`: 0, 2, 4, … 16. With the **`X` shift** (the top-left sea tile stays empty), port *k* is on `2k−1`: 1, 3, … 17.
- Corner ports are therefore #1, #4, #7 (no shift) or #2, #5, #8 (with the shift).

## 3. The string

Everything is one string with **no spaces**.

### 3.1 Parts

| part | content | length |
|---|---|---|
| tiles | 19 letters `W O C S G D` | 19 |
| tokens | 18 symbols from `2345689abc` | 18 |
| ports (optional) | optional `X`, then 9 port symbols | 9 (+1) |

Port symbols: `W O C S G` = 2:1 port of that resource, **uppercase = forward, lowercase `w o c s g` = backward**; **`3`** = 3:1 backward, **`#`** = 3:1 forward. For a corner port the orientation is forced: when writing, use lowercase / `3`; when reading, either case is accepted.

If the ports part is missing, the default is **`3gO3s#3cW`** (no shift). Check: ports 1, 4, 7 are `3` on the corners, and all four 3:1 ports and the five resource ports are present.

### 3.2 Two formats

- **`s` — sections:** tiles, then tokens, then ports.
- **`p` — paired:** each tile letter followed by its token (the desert has none), then ports.

Example (hand-checked: counts are right and no 6/8 touch; not produced by code):

```
s   WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48
s   (with ports)  WSGOCWSGDOWCSGOCWSG563a4b892c563b9a483gO3s#3cW
p   W5S6G3OaC4WbS8G9DO2WcC5S6G3ObC9WaS4G8
```

### 3.3 Separators (`--pipes`)

- Without `--pipes` the string is a single run of characters.
- With `--pipes` the **rows are separated by `|`** and the **parts by `,`**:

```
WSG|OCWS|GDOWC|SGOC|WSG,563|a4b8|92c5|63b9|a48,3gO3s#3cW
W5S6G3|OaC4WbS8|G9DO2WcC5|S6G3ObC9|WaS4G8,3gO3s#3cW
```

Rows follow the board rows; the token rows are shorter by one where the desert is. The ports part has no `|`.

### 3.4 Reading a string

- The reader **removes `|` and `,`** and trims whitespace around the whole string. Any other unexpected character, including a space inside, is an error that names its position.
- **Format detection:** if the first 19 characters are all tile letters it is `s`, otherwise `p`. A paired string has token characters (digits or lowercase letters) among its first 19, so this is never ambiguous.
- After the tiles and tokens, whatever is left is the ports part (empty, or `X` plus 9, or 9).
- **Validation:** exact counts of tiles, tokens and ports; at most one `X` and only at the start; clear messages. Adjacent 6/8 is only a **warning** when reading, not an error.
- Case matters (see 2.2 and 3.1).

## 4. Seeds

- A seed is **letters only, A–Z, case-insensitive** (`kmqxrt` = `KMQXRT`), 1 to 32 letters. Digits and any other character are rejected with a clear message. Letters only means a `0`/`O` or `1`/`I` mix-up cannot happen, a seed can be dictated over the phone, and it can never be confused with the digits of the tokens.
- The RNG is Python's `random.Random`, seeded from the normalized seed text (uppercase): `int.from_bytes(sha256("catan-map-v1:" + SEED).digest(), "big")`. Every distinct text is a distinct seed, any length, and the `v1` prefix lets a future algorithm get its own seeds without changing old ones.
- **A random seed** is **6 letters** by default.

How many seeds there are:

| letters | A–Z (base 26, decided) | for comparison: base 32 | base 36 |
|---|---|---|---|
| 4 | 456,976 | 1,048,576 | 1,679,616 |
| 5 | 11,881,376 | 33,554,432 | 60,466,176 |
| 6 | **308,915,776** | 1,073,741,824 | 2,176,782,336 |
| 7 | 8,031,810,176 | 34,359,738,368 | 78,364,164,096 |
| 8 | 208,827,064,576 | about 1.1 × 10¹² | about 2.8 × 10¹² |

The seed is only a *name* for a board: there are about 6 × 10²⁴ different boards (244 billion tile arrangements × 25 trillion token arrangements, before the 6/8 rule), so a seed reaches a tiny part of them, which is fine. Two **random** 6-letter seeds are likely to coincide only after about 20,700 are made (a 50% chance of one repeat), and a repeat just means the same board again. Seven letters would give 8 billion if that is ever too few.

### 4.1 Seed code: the seed carries its non-default options

The same seed gives the same map only with the same options, and the options change the result (`--desert`, the 6/8 rule, and whether ports are included). So the **seed code** is the seed plus the non-default options, after a `-`:

```
KMQXRT            all defaults
KMQXRT-E          desert on the edge
KMQXRT-I          desert inside (off the edge: center or ring)
KMQXRT-C          desert in the center
KMQXRT-R          desert in the ring (around the center)
KMQXRT-A          adjacent 6/8 allowed
KMQXRT-P          with ports
KMQXRT-RAP        several: the desert letter (E, I, C or R), A, P
```

- Each flag letter means one thing and appears at most once, so **the order carries no meaning**: `-RAP`, `-PAR` and `-APR` are the same, in any case. When the code is **written** (the printed `seed:` line) it always uses one fixed order (desert letter, then `A`, then `P`), so a given code has a single spelling that is easy to compare and share.
- A repeated letter (`-EE`), two desert letters (`-EI`) or an unknown letter is an error.
- Defaults are never written, so a plain seed means all defaults.
- The printed `seed:` line is always the full seed code, so copying it reproduces the whole string, ports included.
- The flags are **not** part of what the RNG is seeded from; they only tell the generator how to behave.
- **A flag in the code is an explicit statement.** A command-line option may *add* an option the code does not mention, but if it **disagrees** with one the code does state, the program **stops with an error** (exit code 2) and changes nothing:

```
--seed KMQXRT --desert edge          fine: same as --seed KMQXRT-E
--seed KMQXRT-E --desert edge        fine: they agree
--seed KMQXRT-E --desert inner       error: the seed code says the desert is on the edge (E),
                                     but --desert inner was given
--seed KMQXRT-A --allow-adjacent-red fine: they agree (A and P have no opposite, so they cannot disagree)
```

- The **string** needs no flags: it describes the board completely, so sharing the string always works.
- `--pipes`, `--format` and `--board` only change how things are shown, so they are not in the code.

## 5. The generator

Only `random.Random.random()` is used, with a **hand-written Fisher–Yates shuffle** (`i` from the end, `j = floor(random() · (i + 1))`). Python promises `random()` stays the same across versions but not `shuffle`, so a seed gives the same map forever.

Order of draws (fixed and documented; the ports come last so `--ports` never changes the tiles or tokens of a seed):

1. **Desert position:** chosen among the allowed tiles (`--desert`), then the other 18 tiles are shuffled over the remaining positions.
2. **Tokens:** shuffled over the non-desert tiles. If the rule is on and a 6 or 8 touches another 6 or 8, shuffle again (the same stream, at most 10,000 attempts, then an error).
3. **Ports** (only with `--ports`): the shift (`random() < 0.5`), then a shuffle of the 9 port types, then the orientation of each non-corner port in order (`random() < 0.5` = forward). Corner ports draw nothing. Then the ports are **moved off the desert** if needed (section 11); that draws nothing more, so the ports always take the same number of draws.

`--desert`:
- `free` (default): any of the 19 tiles.
- `edge`: any of the 12 tiles that touch the sea.
- `inner`: "off the edge": any of the 7 inner tiles (center and ring: 4, 5, 8, 9, 10, 13, 14).
- `center`: only the center tile (9).
- `ring`: any of the 6 tiles around the center (4, 5, 8, 10, 13, 14), that is `inner` without the center.

Not in version 1: other fairness rules (for example no equal numbers next to each other).

## 6. The command line

```
python scripts/catan_map.py                        # random seed: prints the seed and the string
python scripts/catan_map.py --seed KMQXRT
python scripts/catan_map.py --string "WSGOCW...ports"   # read a string instead of a seed
```

| flag | meaning |
|---|---|
| `--seed CODE` | the seed code (section 4.1, letters only, case-insensitive); with neither `--seed` nor `--string`, a random 6-letter seed is made and shown. A code flag that disagrees with a command-line option is an error |
| `--string STR` | read a string (either format, with or without separators) instead of using a seed |
| `--format s\|p` | `s` sections (default) or `p` paired; `sections` and `paired` also work |
| `--pipes` | write rows with `\|` and parts with `,` |
| `--ports` | include the ports part: random ports when making a board from a seed; the default ports when reading a string that has none (a string that has ports always keeps them) |
| `--board` | draw the board in the console |
| `--color` | colors in the drawing (off by default) |
| `--ascii` | the drawing in plain ASCII (this also happens by itself on a console that cannot show the arrows) |
| `--desert free\|edge\|inner\|center\|ring` | where the desert may be (section 5) |
| `--allow-adjacent-red` | allow a 6/8 next to a 6/8 |

Output when generating:

```
seed:   KMQXRT
string: WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48
```

With `--string`, the `seed:` line is left out, the string is shown in the chosen format, and warnings are listed. Bad input prints a message to stderr and exits with code 2.

## 7. The console drawing (`--board`)

The island with its tokens, and the sea ring around it with each port: a letter for a 2:1 port (`G` grain, `O` ore, `S` sheep, `C` clay, `W` wood), `3` for a 3:1 port, `~` for plain water, and an **arrow on the side of the port that faces the island tile it attaches to**. A legend lists every port. Tokens: `a` = 10, `b` = 11, `c` = 12; `D` is the desert.

The board below is the example from section 3.2 with the default ports `3gO3s#3cW`. These drawings were produced by a throwaway script that also checked the ring table of section 2.3 against the tile coordinates, so the arrows are right for that table; the final output will be made by the real code.

**Unicode** (`--board`):

```
         3↘    ~     ↙G    ~
      ~     W5    S6    G3    ↙O
   W→    Oa    C4    Wb    S8    ~
~     G9    D     O2    Wc    C5    ←3
   C→    S6    G3    Ob    C9    ~
      ~     Wa    S4    G8    ↖S
         3↗    ~     ↖3    ~
```

**ASCII** (`--board --ascii`), the same board (`/` and `\` are the slanted arrows, `<` and `>` the sideways ones):

```
         3\    ~     /G    ~
      ~     W5    S6    G3    /O
   W>    Oa    C4    Wb    S8    ~
~     G9    D     O2    Wc    C5    <3
   C>    S6    G3    Ob    C9    ~
      ~     Wa    S4    G8    \S
         3/    ~     \3    ~
```

**Legend** (printed under the drawing):

```
port 1 (ring  0, corner  ): 3:1       -> tile  0 (row 1, col 1)
port 2 (ring  2, backward): 2:1 grain -> tile  1 (row 1, col 2)
port 3 (ring  4, forward ): 2:1 ore   -> tile  6 (row 2, col 4)
port 4 (ring  6, corner  ): 3:1       -> tile 11 (row 3, col 5)
port 5 (ring  8, backward): 2:1 sheep -> tile 15 (row 4, col 4)
port 6 (ring 10, forward ): 3:1       -> tile 17 (row 5, col 2)
port 7 (ring 12, corner  ): 3:1       -> tile 16 (row 5, col 1)
port 8 (ring 14, backward): 2:1 clay  -> tile 12 (row 4, col 1)
port 9 (ring 16, forward ): 2:1 wood  -> tile  3 (row 2, col 1)
```

The same ports with the **`X` shift** (the string `X3gO3s#3cW`), where the ports move to ring 1, 3, 5, … and the corners that hold ports change:

```
         ~     ↙3    ~     ↙G
      W→    W5    S6    G3    ~
   ~     Oa    C4    Wb    S8    ↙O
C→    G9    D     O2    Wc    C5    ~
   ~     S6    G3    Ob    C9    ↖3
      3→    Wa    S4    G8    ~
         ~     ↖3    ~     ↖S
```

**Colors** (`--color`): wood green, ore grey, clay red, sheep light green, grain yellow, desert tan; they are plain ANSI codes and off by default, so output pasted into a file or chat stays clean.

## 8. Code layout: a separate repository

A **repository named `catan-map`, next to `only-games`** (`../catan-map`), to be used by the site later. The utility has no dependency on the site, so it stays small and reusable.

```
catan-map/
    pyproject.toml          package "catan-map", import name catan_map, command `catan-map`
    README.md               how to use it
    docs/PLAN.md            this plan
    catan_map/
        board.py            rows, neighbours, zones, the sea ring and its table (section 2)
        codec.py            write and read the string, validation
        seed.py             seed codes (section 4)
        generator.py        the seeded generator (section 5)
        render_text.py      the console drawing
        cli.py              the command line (section 6); __main__.py runs it
    tests/                  unittest, nothing to install: python -m unittest
```

- **No dependencies at all:** only the Python standard library.
- **Run it** with `python -m catan_map ...` or, after `pip install -e .`, the `catan-map` command.
- **Versions:** release tags (`v1.0.0`). A given seed code must keep giving the same string for every `1.x` release; the algorithm version is also in the seed hashing (`catan-map-v1`). `tests/test_golden.py` holds fixed seeds with their exact strings to catch any change.
- **Tests:** about 110, in `tests/test_board.py`, `test_codec.py`, `test_seed.py`, `test_generator.py`, `test_render.py`, `test_cli.py` and `test_golden.py`.
- **Using it from OnlyGames later:** a line in `requirements.txt` that points at a release tag of the repository (or `-e ../catan-map` while developing), then `from catan_map import generate, parse` in a page or an image route.

## 9. Later

- **Images:** an SVG (no new dependency) or a PNG with Pillow, which the site already uses.
- **The site:** a page like `/tools/catan-map/<seed code>` that shows the board and the string, using the package from the new repository.
- **Bigger islands:** the board layout (row lengths, piece counts, ring) becomes a parameter, with a layout code in the string. Seeds of the standard board must not change.

## 10. Decisions and open questions

**Decided**
- The string has no spaces. `--pipes` separates rows with `|` and parts with `,`. The reader ignores both.
- `--format s` and `--format p`.
- Ports: backward/forward as in 2.3; corner ports are written lowercase/`3`.
- No adjacent 6/8 by default, with a flag to turn it off. `--desert free` (default) / `edge` (12 tiles) / `inner` (7 tiles) / `center` (1 tile) / `ring` (6 tiles).
- The shuffle uses only `random()`. Pipes only in tiles and tokens. Standard 19-tile board first; bigger islands later.
- A **separate repository** named `catan-map` next to `only-games`, created locally with `git init`, with this plan moved into it. The site uses it later.
- A random seed is **6 characters** by default.
- **Seed code flags** (section 4.1): the non-default options travel in the seed after a `-`; the flag letters are unique so their order does not matter when reading, and the code is written in one fixed order. If a code flag and a command-line option **disagree, the program aborts with an error**.
- **Drawing style:** Unicode arrows by default with `--ascii` as the fallback; colors only with `--color`.
- **Seeds are letters only (A–Z)**, case-insensitive, 6 letters by default.
- **A command-line option may add** an option the seed code does not mention, **but may not change** one the code states (that is an error).

**Still open**

Nothing. Version 1.0.0 is built; see section 11 for how it differs from the plan.

## 11. As built: where the tool differs from the plan

- `--string` together with `--desert` or `--allow-adjacent-red` is an **error**: those options only mean something when a board is made from a seed.
- A string that has a ports part always keeps it when it is read and written again; `--ports` only adds the default ports to a string that has none.
- A console whose encoding cannot show the arrows (an old Windows console, `PYTHONIOENCODING=ascii`) gets the ASCII drawing by itself.
- A string made only of separators is reported as empty.
- Seeds are 1 to 32 letters; digits are rejected with a hint that seeds are letters only.
- Checked on 20,000 boards: 0.05 ms per board, no 6/8 ever touches another, every string is different, the desert is spread evenly over the 19 tiles, the ring is shifted about half the time, and the token shuffle needed 7.4 tries on average (68 at most; the limit is 10,000).
- **Rule added after the first version: a port may not attach to the desert.**
  - *Reading:* a string whose ports part has a port on the desert is an error that names the character and the port.
  - *Generating:* after the random draws the ports are moved off the desert with `avoid_desert`: a port that is not on a corner and would attach to the desert switches to its other orientation; if a corner port would, the ring is shifted by one (the corner tiles of the two shifts never overlap, so one of them always works). The draws are unchanged, so tiles and tokens of a seed are not affected, and the ports part of a seed changes only where it used to touch the desert.
  - *No ports part:* the default `3gO3s#3cW` attaches to tiles 0, 1, 3, 6, 11, 12, 15, 16 and 17, so on about half of the boards it would touch the desert. The implied ports are therefore the default moved off the desert in the same way; `--ports` writes them out, and the drawing says "moved off the desert". Otherwise nothing changes.
  - *Tests:* `tests/test_ports_rule.py`; the fixed seeds with ports in `tests/test_golden.py` were updated (`KMQXRT` and `ZZZZZZ`). This was done before the tool was published, so no shared seed changed.
