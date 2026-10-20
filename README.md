# catan-map

A *Settlers of Catan* map generator. A **seed** gives a board; a board is a short **string** you can copy, share and read back; and the board can be drawn in the console. Pure Python, no dependencies.

```
$ python -m catan_map --seed KMQXRT
seed:   KMQXRT
string: CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8
```

The same seed (with the same options) gives the same board on any machine and any Python version, and the string describes the board completely, so sharing the string always works.

## Quick start

```
python -m catan_map                          # a random 3-letter seed: prints the seed and the string
python -m catan_map --seed KMQXRT            # the same seed always gives the same board
python -m catan_map --seed KMQXRT --board    # and draw it
python -m catan_map --string "WSGOCW..."     # read a string instead of using a seed
python -m unittest                           # run the tests
```

All of these start the same program: `python -m catan_map`, `python catan_map/cli.py` (or `uv run catan_map/cli.py`), `uv run catan-map`, and, after `pip install -e .`, the `catan-map` command. The package can also be imported (see [From Python](#from-python)).

## The board

The standard island: 19 land tiles in rows of 3, 4, 5, 4 and 3, scanned left to right, top to bottom.

- **Tiles:** `W` wood, `O` ore, `C` clay, `S` sheep, `G` grain, `D` desert (4 W, 4 S, 4 G, 3 O, 3 C, 1 D).
- **Number tokens:** `2 3 4 5 6 8 9 a b c`, where `a` is 10, `b` is 11 and `c` is 12 (there is no 7): one `2`, one `c`, two of each of the others. The desert has no token.
- **Ports:** 9 of them, four 3:1 and one 2:1 for each resource, on the ring of 18 sea tiles around the island.

By default a **6 or 8 never touches another 6 or 8**, and the **2 and the 12 (`c`) never touch each other**; the `A` flag allows touching 6 and 8, and the `L` flag allows touching 2 and 12. Another rule, off by default, is **no two neighbouring tiles of the same terrain** (the `U` flag).

## The string

One string, no spaces, up to three parts:

| part | content | length |
|---|---|---|
| tiles | the 19 tile letters, row by row | 19 |
| tokens | the 18 tokens, in the same order, skipping the desert | 18 |
| ports (optional) | an optional `X`, then 9 port symbols | 9 (+1) |

Two layouts, chosen with `--format`: **`s`** (sections: tiles, then tokens, then ports) and **`p`** (paired: every tile followed by its token, the desert alone, then ports). By default the rows are separated by `|` and the parts by `,`; `--no-pipes` leaves them out. The reader ignores `|` and `,` and finds the layout by itself.

The same board in every form:

```
s  no pipes  WSGOCWSGDOWCSGOCWSG563a4b892c563b9a48
s  pipes     WSG|OCWS|GDOWC|SGOC|WSG,563|a4b8|92c5|63b9|a48
p  no pipes  W5S6G3OaC4WbS8G9DO2WcC5S6G3ObC9WaS4G8
p  pipes     W5S6G3|OaC4WbS8|G9DO2WcC5|S6G3ObC9|WaS4G8
```

and with ports (`3gO3s#3cW`) added at the end, for example `WSG|OCWS|GDOWC|SGOC|WSG,563|a4b8|92c5|63b9|a48,3gO3s#3cW`.

Tile letters are uppercase and token letters are lowercase, so `C` (clay) and `c` (12) never clash. A bad string gives an error that names the character.

### Ports

The sea ring has 18 tiles, numbered 0-17 clockwise from the top-left corner. The nine ports sit on every second sea tile, with water between them. A leading `X` shifts them by one, so the top-left sea tile is empty.

Port symbols: `W O C S G` are 2:1 ports of that resource, `3` is a 3:1 port. A sea tile that touches two island tiles gives a port two ways to attach: **lowercase** (`w o c s g`, and `3`) attaches it to the first of the two tiles in clockwise order ("backward"), **uppercase** (`W O C S G`, and `#` for 3:1) to the second ("forward"). Ports on the six corner sea tiles have only one way to attach, so their case does not matter when reading, and they are written lowercase.

If the ports part is missing, the default `3gO3s#3cW` is used.

## Seeds

A **seed** is letters only (A-Z), case-insensitive, 1 to 32 letters; a random one is 3 different letters (15,600 of them). A **seed code** adds the options that are not the default, after a `-`, so that the code alone reproduces a whole string:

```
KMQXRT        all defaults (desert in the center)
KMQXRT-E      desert on the edge          (F free, E edge, I inner, C center, R ring: only one; the default is C, so it is not written)
KMQXRT-A      adjacent 6/8 allowed
KMQXRT-L      the 2 and the 12 may touch (they may not, by default)
KMQXRT-U      no two neighbouring tiles of the same terrain (allowed, by default)
KMQXRT-P      the string includes ports
KMQXRT-RALUP  several: the desert letter, then A, L, U, then P
```

The flag letters are unique, so their **order does not matter** when reading; a code is always written in the order above. A command-line option may **add** an option the code does not mention (`--seed KMQXRT --desert edge` is `KMQXRT-E`), but it may **not change** one the code states: that is an error.

## Command line

| option | meaning |
|---|---|
| `--seed CODE` | the seed code; without `--seed` and `--string` a random one is made and printed |
| `--string STR` | read this string instead (either layout, with or without `\|` and `,`) |
| `--format s\|p` | sections or paired (default); `sections` and `paired` also work |
| `--no-pipes` | write the string without the `\|` between rows and the `,` between parts (they are written by default) |
| `--ports` | include the ports part: random ports from a seed; the default ports when reading a string that has none (a string that has ports always keeps them) |
| `--board` | draw the board |
| `--color` | colours in the drawing |
| `--elements [NAMES]` | make the SVG a printable 60 x 60 cm sheet (the board 550 x 505 mm, the number tokens 25 mm across) with these things on it, separated by spaces or commas: `costs` (a Building Costs card in each corner), `bank` (places for the bank along the bottom; the island moves up), `seed` (the seed code, big), `str` (the string, on one line), `logo` (the `--logo-img` image, as large as fits). `all` means all of them; no names means the bare sheet. Needs `--svg` |
| `--logo-img FILE` | the image (png, jpg, gif, webp or svg) for the `logo` element, embedded in the SVG. Needs `--svg` and `--elements` with `logo` |
| `--desert-logo FILE` | an image (png, jpg, gif, webp or svg) for the middle of the desert tile, the size of a number token (25 mm on a sheet), embedded in the SVG. Needs `--svg` |
| `--icons simple\|detailed\|realistic` | the small resource icons (ports, cost cards, bank); realistic is the default. Needs `--svg` |
| `--lang he\|en` | the language of the Building Costs cards: Hebrew (default) or English. Needs `--svg` |
| `--tiles basic\|realistic\|plain\|illustrated` | the look of the tiles in the SVG: `basic` (flat colours, simple shapes), `realistic` (painted-looking, the default), `plain` (one colour per tile) or `illustrated` (pictures of the tiles, each with its own border). Needs `--svg` |
| `--svg FILE` | write the board as an SVG image (`-` prints it to the terminal; the seed and string go to stderr) |
| `--ascii` | draw with plain ASCII (this happens by itself on a console that cannot show the arrows) |
| `--desert free\|edge\|inner\|center\|ring` | where the desert is: the middle tile (default), anywhere, the 12 tiles on the coast, the 7 that do not touch the sea, or the 6 around the middle |
| `--allow-adjacent-red` | allow a 6 or 8 next to another 6 or 8 (`A`) |
| `--allow-adjacent-2-12` | allow the 2 and the 12 next to each other (`L`; they never touch by default) |
| `--no-same-neighbours` | no two neighbouring tiles of the same terrain (`U`; off by default) |

`-h` or `--help` lists all the options. `--desert`, `--allow-adjacent-red`, `--allow-adjacent-2-12` and `--no-same-neighbours` only apply to a board made from a seed. Exit code 0 on success, 2 on bad input (the reason is printed to stderr). A string whose 6 and 8 touch, or whose 2 and 12 touch, is accepted, with a warning on stderr. So is a string with a non-standard mix of tiles, tokens or ports (18 wood, no desert, ...): it only needs 19 tiles, a token for every tile but the desert, and 9 ports if it has any.

### The drawing

```
$ python -m catan_map --seed KMQXRT --board --ports
seed:   KMQXRT-P
string: CGGDWSWWCOGCGOSSOSW2a5ba8456996c433b8XcgW#3#os3

         ~     ↙C    ~     ↙G
      3↘    C2    Ga    G5    ~
   ~     D     Wb    Sa    W8    ↙W
S→    W4    C5    O6    G9    C9    ~
   ~     G6    Oc    S4    S3    ←3
      O→    O3    Sb    W8    ~
         ~     ↖3    ~     ↖3
```

`3` is a 3:1 port and a letter a 2:1 port; the arrow is on the side of the port that faces the island tile it attaches to; `~` is water. `--ascii` uses `/ \ < >` instead of the arrows.

Reading a string whose 6 and 8 touch (this one has the 8 moved next to the 6): it is accepted, with a warning.

```
$ python -m catan_map --string WSGOCWSGDOWCSGOCWSG568a4b392c563b9a48 --format p
string: W5S6G8OaC4WbS3G9DO2WcC5S6G3ObC9WaS4G8
warning: the 6 at row 1, column 2 touches the 8 at row 1, column 3
```

## From Python

```python
from catan_map import generate, serialize, parse, render_board

board = generate("KMQXRT", desert="edge", ports=True)   # a Board
text = serialize(board, fmt="p", pipes=True, include_ports=True)
parse(text).board == board                               # True
print(render_board(board, ascii_only=True))
```

`make` does what the command line does in one call (a board from a seed, a string, or a new random seed, with the string and any warnings), and `render_svg(board, caption, tiles, elements, logo)` draws it:

```python
from catan_map import make, render_svg

made = make("KMQXRT", ports=True)                   # made.board, made.code, made.text, made.warnings, made.caption
svg = render_svg(made.board, made.caption, "realistic", elements=("costs", "seed", "str"))
```

`generate` takes a seed or a `SeedCode`; `parse_seed_code`, `format_seed_code` and `combine` handle seed codes; every error derives from `CatanMapError`.

## Printing the sheet on A4 pages

`scripts/svg_to_pages.py` cuts a big SVG, such as the 60 x 60 cm sheet, into the pages of one PDF, to print on A4 and tape together. It needs Chrome, Chromium or Edge (set `CHROME` to its path if it is not found), which keeps the drawing as vectors.

```bash
python -m catan_map --seed KMQXRT-P --svg sheet.svg --elements all
python scripts/svg_to_pages.py sheet.svg              # sheet-pages.pdf: 6 A4 pages (3 across, 2 down)
python scripts/svg_to_pages.py sheet.svg --scale 1    # real size: 9 pages
```

Six A4 pages cannot hold 60 cm at real size (2 pages of 29.7 cm are 59.4 cm, and a printer leaves a margin around every page), so by default the sheet is shrunk to fit six pages, about 96% with 5 mm margins; `--scale 1` prints the real size on nine. The pages are cut exactly where the printable area ends: trim the margins (or fold them under) and the pages meet edge to edge. Corner marks and a "column 2, row 1" label are in the margins; `--no-marks` leaves them out. Other options: `--margin MM` (the printer's unprinted margin), `--paper A3|LETTER`, `--pages N`, `-o FILE`.

## How the generator works

Only `random.Random.random()` is used, with a hand-written Fisher-Yates shuffle. Python guarantees the sequence of `random()` for a given seed, but not the algorithm of `shuffle`, so a seed gives the same board forever. The seed text is hashed (`sha256("catan-map-v1:" + SEED)`) into the generator's seed. The draws are made in a fixed order, and the ports come last, so asking for ports never changes the tiles or the tokens of a seed:

1. the desert's position among the tiles its option allows, then the other 18 tiles shuffled over the rest (with `U`, placed one by one so that no neighbours match: a shuffle with no matching neighbours is about 1 in 1,300, too rare to wait for);
2. the tokens, reshuffled until no 6 or 8 touches another (unless allowed) and the 2 and 12 do not touch (unless allowed);
3. the ports: whether the ring is shifted, a shuffle of the nine types, then the orientation of each port that is not on a corner.

`tests/test_golden.py` holds fixed seeds with their exact strings; if one fails, the generator changed, which would break every seed anyone has shared.

## The icons

The small resource icons (on the port badges, the cost cards and the bank slots) come in three sets (`catan_map/icons.py`): `simple` (flat, the first look), `detailed` (flat, more shapes) and **`realistic`** (painted-looking, the default). `--icons simple|detailed|realistic` chooses (with `--svg`), and `render_svg(..., icons="simple")` in Python. The realistic gradients are defined once in the drawing, however many icons use them; the realistic set adds about 140 KB to a sheet. `docs/icons-comparison.svg` (made by `python scripts/make_icon_comparison.py`) shows the three sets side by side.

## Ideas for later

Bigger boards (5-6 players), Cities & Knights and Seafarers are not built; what each would change, the order to do them in and the open questions are in [`docs/IDEAS.md`](docs/IDEAS.md).

## Layout

```
catan_map/
    board.py           the island: rows, neighbours, zones, the sea ring and its table
    codec.py           writing and reading the string
    seed.py            seed codes
    generator.py       the seeded generator
    render_text.py     the console drawing
    cli.py             the command line
tests/                 unittest, nothing to install: python -m unittest
docs/PLAN.md           the plan this was built from
```

Later: images (SVG), a page on the OnlyGames site, and bigger islands (the layout would become a parameter, with seeds of the standard board unchanged).
