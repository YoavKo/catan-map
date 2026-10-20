"""Drawing a board as an SVG image.

Hexagons are pointy-top with radius 100, so a step of 1 in the board's x coordinate is half a
hexagon wide, and a row is 1.5 radii lower than the one above. The island, the ring of sea
around it and the ports use the same positions as the console drawing. The output is plain
text and always the same for the same board.
"""
from __future__ import annotations

import base64
from pathlib import Path
from xml.sax.saxutils import escape

from .board import (
    RING_POSITIONS,
    RING_SIZE,
    TILE_COUNT,
    RED_TOKENS,
    TILE_POSITIONS,
    TOKEN_VALUES,
    direction,
    port_ring_position,
    port_target_tile,
)
from .codec import CatanMapError
from .imagesize import data_uri_size
from .icons import check_icon_set
from .svg_cards import BANK_BOX, CARD_HEIGHT, CARD_WIDTH, bank_group, building_costs_card, check_language
from .svg_tiles import get_tile_set, port_group, tile_defs
from .tiles_common import HALF_WIDTH, OUTLINE, RADIUS

ROW_STEP = RADIUS * 1.5
MARGIN = 24

# The sea is cut to a regular hexagon (flat top and bottom) through the notches of the ring of sea tiles: its top and
# bottom edges are at the shoulders of the top and bottom sea rows, so the points of the tiles outside it are cut off.
OUTLINE_TOP, OUTLINE_BOTTOM = -(ROW_STEP + RADIUS / 2), 5 * ROW_STEP + RADIUS / 2
OUTLINE_HALF_HEIGHT = (OUTLINE_BOTTOM - OUTLINE_TOP) / 2
OUTLINE_CENTER_Y = (OUTLINE_BOTTOM + OUTLINE_TOP) / 2
OUTLINE_HALF_WIDTH = OUTLINE_HALF_HEIGHT * 2 / 3 ** 0.5       # its left and right points
SEA_OUTLINE = " ".join(
    f"{x:.3f},{y:.3f}" for x, y in (
        (-OUTLINE_HALF_WIDTH / 2, OUTLINE_TOP), (OUTLINE_HALF_WIDTH / 2, OUTLINE_TOP), (OUTLINE_HALF_WIDTH, OUTLINE_CENTER_Y),
        (OUTLINE_HALF_WIDTH / 2, OUTLINE_BOTTOM), (-OUTLINE_HALF_WIDTH / 2, OUTLINE_BOTTOM), (-OUTLINE_HALF_WIDTH, OUTLINE_CENTER_Y),
    )
)
CAPTION_LINE = 34
BACKGROUND = "#f7f3e3"
TOKEN_RADIUS = 31
DESERT_LOGO_TOKENS = 2.4      # the logo in the desert is this many tokens across (the tile is 173 units wide)
# The number on a token: large, on a token that keeps its size. The pips sit under it.
DIGIT_SIZE = 35         # one digit (2 to 9)
DIGIT_SIZE_WIDE = 29    # 10, 11, 12
DIGIT_BASELINE = 9
PIP_Y = 21

# The printed mat (--elements): a square sheet, with the board and the tokens at a real size, in mm.
# --elements says what else is on it: these, in any number.
ELEMENTS = ("costs", "bank", "seed", "str", "logo")
MAT_MM = 600
BOARD_MM = (550, 505)     # the board (with its sea) is drawn as large as fits in this
TOKEN_MM = 25             # the diameter of a number token
FRAME = 5                 # mm: the gold frame round the sheet
INSET = FRAME + 3         # mm: nothing but the frame is closer to the edge than this
CARD_MARGIN = INSET
# the seed and string above the bottom right card, right-aligned, under the logo
STACK_RIGHT = MAT_MM - INSET       # mm
STACK_WIDTH = 97        # the free width above the card: the island's sea ends 498 mm from the left
SEED_SIZE = 24          # mm: the seed is big, to be read from across the table; a long code is written smaller to fit
STRING_SIZE = 6.4       # mm: the size the string would be, about twice a whole string on one line over the card...
STRING_MIN = 2.5        # ...but it is kept on one line, so it is made as large as the room allows, down to this
SEED_BASELINE = 506     # the baseline of the seed, just above the bottom right card (when the card is there)
SEED_BASELINE_FREE = 585    # and when there is no card
SEED_GAP = 3            # mm between the string and the seed under it
GLYPH = 0.6             # the width of a monospace character, as a fraction of its size
LOGO_BOX = (495, 415, 97, 70)       # x, y, width, height in mm: used when the shape of the logo is not known
LOGO_GAP = 4            # mm between the logo and the island
CARD_BOTTOM = 128       # the top right card (turned) ends here; the logo stays below it
SEED_CAP = 0.75         # the height of the seed's capital letters, as a fraction of its size
LOGO_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
              ".webp": "image/webp", ".svg": "image/svg+xml"}
# the four cards, turned to face the four sides of the table: (corner, turn in degrees)
CARD_PLACES = (("top-left", 180), ("top-right", 270), ("bottom-left", 90), ("bottom-right", 0))


def _center(row, x):
    return x * HALF_WIDTH, row * ROW_STEP


def _frame():
    """The gold frame round the sheet, FRAME mm wide: a brushed-gold band (a gradient with a little grain)."""
    outer, inner = MAT_MM, MAT_MM - 2 * FRAME
    ring = f"M0,0H{outer}V{outer}H0Z M{FRAME},{FRAME}V{FRAME + inner}H{FRAME + inner}V{FRAME}Z"
    return (
        '<defs><linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#e9c85a"/><stop offset="0.35" stop-color="#c79a2a"/>'
        '<stop offset="0.6" stop-color="#f0d577"/><stop offset="1" stop-color="#b98a22"/></linearGradient>'
        '<filter id="gold-grain" x="0" y="0" width="100%" height="100%">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.02 0.9" numOctaves="2" seed="3"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 0.45  0 0 0 0 0.3  0 0 0 0 0.05  0 0 0 1.4 -0.45"/><feComposite in2="SourceGraphic" operator="in"/></filter></defs>'
        f'<g id="frame"><path d="{ring}" fill="url(#gold)" fill-rule="evenodd"/>'
        f'<path d="{ring}" fill-rule="evenodd" filter="url(#gold-grain)" opacity="0.35"/></g>'
    )


def _num(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _token(symbol, x, y, tile_set, scale=1.0):
    value = TOKEN_VALUES[symbol]
    red = symbol in RED_TOKENS
    ink = "#c0261d" if red else "#2b2b2b"
    pips = 6 - abs(7 - value)
    pip_x = [(i - (pips - 1) / 2) * 7 for i in range(pips)]
    dots = "".join(f'<circle cx="{_num(dx)}" cy="{PIP_Y}" r="2.3" fill="{ink}"/>' for dx in pip_x)
    zoom = f" scale({scale:.4f})" if scale != 1 else ""
    return (
        f'<g transform="translate({_num(x)} {_num(y)}){zoom}">'
        + (f'<circle cx="2.5" cy="3.5" r="{TOKEN_RADIUS}" fill="#000000" opacity="0.32"/>' if tile_set.shadows else "")
        + f'<circle r="{TOKEN_RADIUS}" fill="{tile_set.token_fill}" stroke="{OUTLINE}" stroke-width="2.5"/>'
        f'<text y="{DIGIT_BASELINE}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="{DIGIT_SIZE if value < 10 else DIGIT_SIZE_WIDE}" '
        f'font-weight="bold" fill="{ink}">{value}</text>'
        f'{dots}</g>'
    )


def logo_data_uri(path):
    """The image file at `path` as a data: URI, so that the SVG holds the logo itself."""
    path = Path(path)
    kind = LOGO_TYPES.get(path.suffix.lower())
    if kind is None:
        raise CatanMapError(f"cannot use {path} as a logo: its type must be one of {', '.join(LOGO_TYPES)}")
    try:
        data = path.read_bytes()
    except OSError as error:
        raise CatanMapError(f"cannot read the logo {path}: {error.strerror or error}") from error
    return f"data:{kind};base64,{base64.b64encode(data).decode('ascii')}"


def _island_edge(shift, scale, y):
    """The furthest right the island (the sea tiles around it) reaches at height y of the sheet, in mm."""
    right = 0.0
    for position in range(RING_SIZE):
        row, x = RING_POSITIONS[position]
        centre_x = MAT_MM / 2 + x * HALF_WIDTH * scale
        dy = abs(y - (shift + row * ROW_STEP * scale)) / scale        # in the board's units
        if dy > RADIUS:
            continue
        half = HALF_WIDTH if dy <= RADIUS / 2 else HALF_WIDTH * (RADIUS - dy) / (RADIUS / 2)
        right = max(right, centre_x + half * scale)
    return right


def fit_logo(aspect, shift, scale, bottom, top_limit=CARD_BOTTOM + LOGO_GAP, bank_right=None):
    """The largest box of the logo's shape (width / height = aspect) that fits in the free corner:
    its right side at the right margin, its bottom at `bottom`, clear of the island and of the
    top right card, and, if `bank_right` is given (the right end of the bank strip, in mm), of the bank. Returns
    (x, y, width, height) in mm, or None if nothing fits."""
    right = STACK_RIGHT
    height = bottom - top_limit
    while height >= 10:
        width = aspect * height
        top = bottom - height
        left = right - width
        edge = max(_island_edge(shift, scale, top + step * (height / 40)) for step in range(41))
        if bank_right is not None and bottom > BANK_BOX[1]:      # the logo reaches down to the bank: stay right of it
            edge = max(edge, bank_right)
        if left >= edge + LOGO_GAP:
            return left, top, width, height
        height -= 0.5
    return None


def stack_layout(seed, string, shift, scale, base=SEED_BASELINE):
    """Where the seed and the string go in the bottom right corner, one under the other: the
    seed with its baseline at `base`, and above it the string, on one line (either may be
    empty). Returns (the seed's size, its baseline, the string's size, its baseline, the top of
    the stack), in mm. The string is as large as fits between the right margin and the island,
    but at most STRING_SIZE."""
    seed_size = min(SEED_SIZE, STACK_WIDTH / (GLYPH * len(seed))) if seed else SEED_SIZE
    seed_top = base - SEED_CAP * seed_size if seed else base
    string_size, string_baseline = 0.0, None
    if string:
        string_baseline = seed_top - SEED_GAP if seed else base
        string_size = STRING_SIZE
        while string_size > STRING_MIN:
            left = STACK_RIGHT - 1 - GLYPH * string_size * len(string)
            top = string_baseline - SEED_CAP * string_size
            edge = max(_island_edge(shift, scale, top + (string_baseline - top) * k / 10) for k in range(11))
            if left >= edge + LOGO_GAP:
                break
            string_size -= 0.1
        top = string_baseline - SEED_CAP * string_size
    else:
        top = seed_top
    return seed_size, base, round(string_size, 2), string_baseline, top


def check_elements(elements):
    """The elements as a tuple, or CatanMapError when one is not known."""
    elements = tuple(elements)
    unknown = [name for name in elements if name not in ELEMENTS]
    if unknown:
        raise CatanMapError(f"unknown element {unknown[0]!r}; the elements are {', '.join(ELEMENTS)}")
    return elements


def _mat_card(corner, turn, tile_set, lang=None, icons=None):
    """One building-costs card, turned by `turn` degrees, in a corner of the mat."""
    sideways = turn in (90, 270)
    width, height = (CARD_HEIGHT, CARD_WIDTH) if sideways else (CARD_WIDTH, CARD_HEIGHT)
    x = CARD_MARGIN + width / 2 if "left" in corner else MAT_MM - CARD_MARGIN - width / 2
    y = CARD_MARGIN + height / 2 if "top" in corner else MAT_MM - CARD_MARGIN - height / 2
    return (
        f'<g transform="translate({_num(x)} {_num(y)}) rotate({turn}) translate({-CARD_WIDTH / 2:g} {-CARD_HEIGHT / 2:g})">'
        f'{building_costs_card(tile_set.name, lang, icons)}</g>'
    )


def render_svg(board, caption=(), tiles=None, elements=None, logo=None, lang=None, icons=None, desert_logo=None):
    """The board as an SVG document (text). `caption` is the seed code and the string (or just
    the string); `tiles` is the name of the tile set ("classic", "victory" or "plain"; the
    default if None).

    With `elements` None the image is the board with the caption under it. With `elements`, a
    list of names from ELEMENTS (it may be empty), it is a printable sheet instead:
    MAT_MM x MAT_MM millimetres, the board as large as fits in BOARD_MM and the number tokens
    TOKEN_MM across, and these things on it:

    costs  a Building Costs card in each corner, turned toward its side of the table, in `lang`
           ("he", the default, or "en")
    bank   places for the resource cards and the development cards along the bottom edge
           (the island moves up to make room)
    seed   the seed code, big, in the bottom right corner
    str    the string, on one line, above the seed
    logo   the image `logo` (a data: URI, see logo_data_uri), as large as fits, above them"""
    tile_set = get_tile_set(tiles)
    lang = check_language(lang)
    icons = check_icon_set(icons)
    mat = elements is not None
    elements = check_elements(elements) if mat else ()
    costs, bank = "costs" in elements, "bank" in elements
    if "logo" in elements and logo is None:
        raise CatanMapError("the logo element needs a logo image")
    ports = board.effective_ports()
    port_at = {}
    for slot, port in enumerate(ports.entries):
        position = port_ring_position(slot, ports.shifted)
        way = direction(position, port_target_tile(slot, ports.shifted, port.forward))
        port_at[position] = (port.kind, way)

    # the board is drawn in its own units (a tile is 200 high) and scaled for the mat
    # (the sea is cut to one big hexagon, so the board is smaller than the ring of sea tiles; the scale is still the one
    # that fits the ring in BOARD_MM, so the tiles and tokens keep their size)
    ring_width = 14 * HALF_WIDTH
    ring_top, ring_bottom = -(ROW_STEP + RADIUS), 5 * ROW_STEP + RADIUS
    scale = min(BOARD_MM[0] / ring_width, BOARD_MM[1] / (ring_bottom - ring_top)) if mat else 1.0
    board_top, board_bottom = OUTLINE_TOP, OUTLINE_BOTTOM
    token_scale = (TOKEN_MM / 2 / scale) / TOKEN_RADIUS if mat else 1.0

    sea = []
    for position in range(RING_SIZE):
        x, y = _center(*RING_POSITIONS[position])
        if position in port_at:
            kind, way = port_at[position]
            sea.append(port_group(kind, way, _num(x), _num(y), tile_set.name, icons))
        else:
            sea.append(f'<use href="#sea" x="{_num(x)}" y="{_num(y)}"/>')

    land, dark, light, tokens, desert_logos = [], [], [], [], []
    for tile in range(TILE_COUNT):
        x, y = _center(*TILE_POSITIONS[tile])
        if not tile_set.own_edges:
            dark.append(f'<use href="#edge-dark" x="{_num(x)}" y="{_num(y)}"/>')
            light.append(f'<use href="#edge-light" x="{_num(x)}" y="{_num(y)}"/>')
        land.append(f'<use href="#tile-{board.tiles[tile]}" x="{_num(x)}" y="{_num(y)}"/>')
        if board.tokens[tile] is not None:
            tokens.append(_token(board.tokens[tile], x, y, tile_set, token_scale))
        elif desert_logo and board.tiles[tile] == "D":
            side = DESERT_LOGO_TOKENS * 2 * TOKEN_RADIUS * token_scale   # a few tokens across: nearly the width of the tile
            desert_logos.append(
                f'<image x="{_num(x - side / 2)}" y="{_num(y - side / 2)}" width="{_num(side)}" height="{_num(side)}" '
                f'preserveAspectRatio="xMidYMid meet" href="{desert_logo}"/>'
            )
    drawing = (
        f'<clipPath id="clip-sea-outline"><polygon points="{SEA_OUTLINE}"/></clipPath>'
        f'<g id="water" clip-path="url(#clip-sea-outline)">{"".join(sea)}</g>'
        f'<g id="edges">{"".join(dark)}{"".join(light)}</g>'
        f'<g id="land">{"".join(land)}</g>'
        f'<g id="tokens">{"".join(tokens)}</g>'
        + (f'<g id="desert-logo">{"".join(desert_logos)}</g>' if desert_logos else "")
    )
    description = " | ".join(caption) if caption else "A Settlers of Catan board"
    head = f'<title>Catan board</title><desc>{escape(description)}</desc>{tile_defs(tile_set.name, icons)}'

    if mat:
        # the island is centred on the sheet, or with a bank moved up to leave room under it
        # the island is in the middle of the free space: of the sheet, or, with the bank, of what is above the bank
        middle = (INSET + BANK_BOX[1]) / 2 if bank else MAT_MM / 2
        shift = middle - (board_top + board_bottom) / 2 * scale
        cards = "".join(_mat_card(corner, turn, tile_set, lang, icons) for corner, turn in CARD_PLACES) if costs else ""
        # without the cost cards the bank moves left, to the margin, to leave the corner to the logo
        bank_dx = 0 if costs else CARD_MARGIN - BANK_BOX[0]
        bank_strip = f'<g transform="translate({bank_dx} 0)">{bank_group(tile_set.name, icons)}</g>' if bank and bank_dx else (bank_group(tile_set.name, icons) if bank else "")
        seed = caption[0] if "seed" in elements and len(caption) > 1 else ""
        string = caption[-1] if "str" in elements and caption else ""
        seed_size, seed_baseline, string_size, string_baseline, stack_top = stack_layout(
            seed, string, shift, scale, SEED_BASELINE if costs else SEED_BASELINE_FREE
        )
        captions = (
            (f'<text x="{STACK_RIGHT - 1}" y="{_num(seed_baseline)}" text-anchor="end" font-family="Consolas, Menlo, monospace" '
             f'font-size="{_num(seed_size)}" fill="#2b2b2b">{escape(seed)}</text>' if seed else "")
            + (f'<text x="{STACK_RIGHT - 1}" y="{_num(string_baseline)}" text-anchor="end" font-family="Consolas, Menlo, monospace" '
               f'font-size="{_num(string_size)}" fill="#2b2b2b">{escape(string)}</text>' if string else "")
        )
        picture = ""
        if "logo" in elements:
            box_x, box_y, box_w, box_h = LOGO_BOX
            size = data_uri_size(logo)
            if size:
                fitted = fit_logo(
                    size[0] / size[1], shift, scale, stack_top - LOGO_GAP,
                    CARD_BOTTOM + LOGO_GAP if costs else CARD_MARGIN,
                    BANK_BOX[0] + BANK_BOX[2] + bank_dx if bank else None,
                )
                if fitted:
                    box_x, box_y, box_w, box_h = (round(v, 2) for v in fitted)
            picture = (
                f'<image x="{box_x}" y="{box_y}" width="{box_w}" height="{box_h}" '
                f'preserveAspectRatio="xMaxYMax meet" href="{logo}"/>'
            )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MAT_MM} {MAT_MM}" width="{MAT_MM}mm" height="{MAT_MM}mm">'
            f'{head}<rect width="{MAT_MM}" height="{MAT_MM}" fill="{BACKGROUND}"/>'
            f'<g transform="translate({MAT_MM / 2:g} {_num(shift)}) scale({scale:.5f})">{drawing}</g>'
            f'{cards}{bank_strip}{captions}{picture}{_frame()}</svg>\n'
        )

    left = -OUTLINE_HALF_WIDTH - MARGIN
    top = board_top - MARGIN
    width = 2 * (OUTLINE_HALF_WIDTH + MARGIN)
    full_height = board_bottom - top + MARGIN   # bottom of row 5 plus margin
    height = full_height + (len(caption) * CAPTION_LINE + MARGIN if caption else 0)

    captions = "".join(
        f'<text x="{_num(left + width / 2)}" y="{_num(top + full_height + CAPTION_LINE * (i + 0.6))}" '
        f'text-anchor="middle" font-family="Consolas, Menlo, monospace" font-size="{24 if i == 0 else 18}" '
        f'fill="#2b2b2b">{escape(line)}</text>'
        for i, line in enumerate(caption)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{_num(left)} {_num(top)} {_num(width)} {_num(height)}" '
        f'width="{_num(width / 2)}" height="{_num(height / 2)}">'
        f'{head}'
        f'<rect x="{_num(left)}" y="{_num(top)}" width="{_num(width)}" height="{_num(height)}" fill="{BACKGROUND}"/>'
        f'{drawing}{captions}</svg>\n'
    )
