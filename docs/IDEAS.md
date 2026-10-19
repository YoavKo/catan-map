# Ideas for later: bigger boards, Cities & Knights, Seafarers

Nothing here is built. This is a place to keep the ideas, what each one would change in the code, and the questions that have to be decided first. Where this note states a rule of the game from memory, it says **(check)**: look it up in the rulebook before building on it.

## 1. Ground rules that every idea must keep

These come from how the tool is used today, and they decide how the new boards can be added.

1. **A seed always gives the same board.** Every seed anyone has shared must keep working. So the standard 19-tile board keeps its algorithm (`catan-map-v1`) untouched, and the golden tests in `tests/test_golden.py` stay as they are. A new kind of board gets its own algorithm name and its own golden tests.
2. **Only what changes the board goes in the seed code.** The seed code is the seed plus the flags that change the string (the desert zone `F E I C R`, adjacent 6/8 `A`, ports `P`). Things that only change how a board is *shown* (`--format`, `--no-pipes`, `--tiles`, `--elements`, the sheet) are not in the code. This decides where each idea below goes: a bigger board and Seafarers change the board, so they are part of the code; Cities & Knights does not change the board, so it is a presentation option.
3. **Old strings keep being readable.** A string for the standard board has no prefix and stays valid forever. A new kind of board announces itself in the string (see 2.2).
4. **The reader is strict about structure and gentle about content.** Wrong lengths and bad characters are errors; an unusual mix of tiles is only a warning. This is what lets a string with 18 woods be drawn, and it should stay so for the new boards.

## 2. Groundwork: boards as data

Today the standard island is built into `board.py` (the rows `3,4,5,4,3`, the 18-tile sea ring, the 9 port slots, the zones for the desert). All three ideas need the same first step, so it should be done once, before any of them.

### 2.1 What has to become data

A **board kind** is a description of one shape of board:

- the rows of land tiles, and so the tile positions and which tiles are neighbours;
- the sea frame around it, and which land tiles each frame tile touches (`RING_TOUCHES`);
- the port slots on the frame, and which of them are corners (a port on a corner has one way to attach);
- the tile mix (how many of each terrain) and the token mix;
- the zones the desert option uses (`edge`, `inner`, `center`, `ring`), which come out of the shape by themselves;
- the size the drawing needs.

The standard board becomes the kind `standard`; the code that uses `ROWS`, `TILE_POSITIONS`, `RING_POSITIONS`, `PORT_COUNT` and the rest asks the kind instead of the module constants. The tests for the standard board must pass unchanged. That is the proof that nothing moved.

### 2.2 The string needs a kind

The string for the standard board is `tiles + tokens + ports` (paired or in sections). For another kind it needs a short prefix that says which, for example `L:...` for the large board. No prefix means `standard`, so nothing old changes. The reader checks the counts against the kind it found, and the `character N` messages keep working because the prefix is counted like any other character. A separate letter (instead of `L:`) is possible too; the point is that a reader can tell the kind from the first characters.

### 2.3 The seed code needs a kind

A flag for the kind (for example `-L`) fits the present form `KMQXRT-L`, `KMQXRT-LP`. The flag letters `F E I C R A P` are taken, so the new letters must be different ones (and one letter must keep meaning one thing). A seed with no kind flag is the standard board.

### 2.4 The algorithm gets a version per kind

`Stream` seeds the random numbers from `"catan-map-v1:" + seed`. A new kind uses its own name in that place (for example `catan-map-large-v1`), so that `KMQXRT` as a large board is a different board from `KMQXRT` as a standard one, and neither can ever change by accident.

### 2.5 The drawing

`render_svg` and the sheet use the geometry of the kind. The sheet is 60 x 60 cm with the board 550 x 505 mm and the tokens 25 mm; a bigger board at the same tile size does not fit in that, so either the board gets smaller tiles on the same sheet (the token stays 25 mm, so the tile would be about 60 mm across and the token fills more of it) or the sheet gets a bigger size. That is a decision (see the questions at the end). The bank strip, the logo box and the stack of seed and string are placed around the island, so they must be placed from the kind's size and not from the numbers that are in the code today.

## 3. The 5-6 player board

### 3.1 What it is

The 5-6 player extension makes the island bigger, so that more players have room. It adds **11 land tiles** to the 19, for **30**: **(check)** 6 forest, 6 pasture, 6 fields, 5 hills, 5 mountains and 2 deserts. The number tokens go from 18 to **28** **(check)**: one more 2 and one more 12 than the standard board has, and one more of each of the others, so 2 and 12 have two each and the other numbers three each. The island is wider; a layout of rows `3,4,5,6,5,4,3` has exactly the 30 tiles **(check the real layout of the frame)**. The ports change too: more of them, and a different mix **(check)**.

### 3.2 What changes in the tool

- **A board kind** for it, as in section 2: the rows, the frame, the port slots, the tile and token mix.
- **Two deserts.** The desert option (`F E I C R`) has to say what it means for two deserts: both in the zone, or one in the zone and one free. The simple rule, both in the zone, is the first thing to try. With two deserts the token string has two fewer entries than the tile string, which the paired layout and the reader already handle (it counts the tokens from the non-desert tiles); the tests with two deserts are there already.
- **The red numbers.** More 6 and 8 tokens (three of each, **(check)**) make "no 6 or 8 next to another" harder to satisfy; the retry limit in `generator.py` (10,000 tries) must be checked on the new shape, and the 2/12 rule must be too.
- **Ports.** The ring is longer, so there are more port slots. The rules about corner slots and the two ways to attach carry over unchanged, but the number of slots and the mix come from the kind.
- **Size.** The island is bigger, so see 2.5.
- **The pieces.** The bank grows (more cards of each resource in the 5-6 player box **(check the number)**). The bank strip on the sheet shows only places for piles, so it does not have to change, but the costs card is the same.

### 3.3 Tests

Golden strings for a few seeds; counts of tiles and tokens; no touching reds and no touching 2 and 12 over a few thousand seeds; the desert zones with two deserts; strings with and without ports round-trip; the reader's messages name the right character with a prefix in front.

## 4. Cities & Knights

### 4.1 What it is

Cities & Knights is a rules expansion for the **same island**: the 19 tiles and the numbers are the ones of the base game, so **the board and its string do not change**. What it adds is pieces and tracks: commodities (cloth from pasture, coin from mountains, paper from forest **(check)**), knights, city walls, city improvements in three tracks, the barbarians (a ship that moves along a track and attacks), progress cards, and an event die.

### 4.2 What it means for the tool

Since the board is the same, **it is not a seed flag** (ground rule 2). It is a presentation option, and the parts of the printed sheet are new `--elements`:

- **`barbarians`**: the barbarian track, drawn like the other elements at a place that clears the island.
- **`improvements`**: the chart of the three improvement tracks.
- **`costs`** gets a second card with the Cities & Knights costs (knights, walls, improvements); the numbers are **(check)** against the rulebook. The `costs` element would take the set to draw (`base`, `knights`).
- **`bank`**: three more places, for cloth, coin and paper; the strip has six slots at the card size today, so nine slots do not fit in a row at that size. Either the commodities get a second, smaller row, or the slots shrink, or the commodities are shown as a separate element.

The commodity icons (cloth, coin, paper) are new artwork in the three tile sets, in the same way as the five resource icons are drawn now.

In the command line this could be a `--game` option (`base`, `knights`) that chooses the sets, next to `--elements`; on the website, a drop-down in the image settings. Because it does not touch the seed, a saved map of an event needs no new field for it.

### 4.3 Tests

The sheet has the new elements and only when asked for; the base sheet is byte for byte what it is now; the new cards say what the rulebook says (a test that holds the costs as data, so that a wrong number is one line to fix).

## 5. Seafarers

### 5.1 What it is

Seafarers adds the sea inside the board: **ships**, **sea tiles** among the land, **gold fields** (a roll gives the player any resource they choose), the **pirate**, harbours on land, and a bonus for settling a new island. It is played on **scenarios**, and most of them are fixed layouts: a shape, which tiles are land and which sea, and often which tiles are placed face down or at random inside given places. A few (for example the one with the islands in a random sea) are built at random.

### 5.2 Why it is the largest idea

It changes things that all the other ideas leave alone:

- **The board is no longer a rows-of-tiles island with a frame.** It is a shape with sea tiles in it, so a tile has a new kind (**sea**), and a land tile can touch the sea in many places. A scenario is a **template**: positions with a type each (land, sea, either), the counts for what goes in the land places, the token mix, the ports, and the special marks (for example a place that is a start place or a bonus island).
- **Two new tile letters.** `S` is already sheep, so sea and gold need other letters; this must be decided with the string (see 5.3). The console drawing and the tile sets (basic, realistic, plain) need artwork for the sea tile and for gold.
- **Ports sit on land edges**, not on a frame of sea tiles. The "sea ring with port slots" of the standard board does not apply, so the port code needs its own version of the rule: a port is on a coast edge of a land tile, and two land tiles' coasts can share it.
- **Rules about what makes a good board** are not the same as for the standard island. For the random scenarios, what counts as valid (for example every island has at least some size, the islands are not joined, the start area is land) has to be written down and tested.
- **Scenarios are data**, like the board kinds of section 2, but with more in them. A good first step is **one fixed scenario** done completely (a layout in a file, with the random parts only in the tile and token assignment), which makes the generator, the string and the drawing work for a sea tile, before any scenario with a random sea.

### 5.3 The string

The prefix of section 2.2 says "Seafarers, scenario N". The tile letters are the standard ones plus two, and the tile string is as long as the scenario's number of places (land and sea). Tokens are given for the land tiles that carry one (not the desert, not the sea). The ports are listed for the scenario's port places. The reader checks against the scenario it found.

### 5.4 The seed code and the algorithm

The scenario goes in the seed code as a flag or a short name; the algorithm name carries the scenario (`catan-map-seafarers-<scenario>-v1`). A scenario that is only partly random draws its random parts in a fixed order, as the standard generator does, so that adding ports (or any later option) never changes the tiles.

### 5.5 The sheet

The island is a different shape and often larger, so the sheet size is a decision again (see the questions). The seed element, the string element, the logo and the bank follow the same placing code as in 2.5. The costs card has the ship (one wood and one wool **(check)**), and the pirate has no piece on the sheet.

### 5.6 Tests

A fixed scenario gives the same board for a seed forever (golden tests); every generated board follows the scenario (the tile counts, the sea where the template says sea); the reader rejects a string for another scenario with a message that names it; the drawing has the sea and gold tiles in the three sets.

## 6. Suggested order

1. **Board kinds as data** (section 2), with the standard board as the only kind and every existing test passing unchanged.
2. **The 5-6 player board** (section 3): the first real second kind, and the proof that the groundwork is right.
3. **Cities & Knights elements** (section 4): independent of the board work, so it can be done at any point after step 1 (even before the 5-6 board).
4. **One Seafarers scenario** (section 5): fixed layout, sea and gold tiles, ports on coasts.
5. **More Seafarers scenarios**, including a random sea.

The website follows each step: the kind (and later the scenario) becomes a drop-down in the map settings, the saved maps of an event (`event_maps`) get a column for the kind, and the `catan-map` pin in `requirements.txt` moves to the new commit.

## 7. Open questions

1. **Letters.** Which letters for the sea tile and the gold field (not `S`, `W`, `O`, `C`, `G`, `D`), for the kind prefix in the string, and for the kind flag in the seed code (not `F E I C R A P`)?
2. **Two deserts.** In the 5-6 player board, may the two deserts be anywhere in the zone, or must they be apart? Should one of them be allowed to be next to the other?
3. **The sheet.** For a bigger board, keep the 60 x 60 cm sheet with smaller tiles, or make the sheet bigger (and the A4 pages, which today are six, become more)? Is the board size 550 mm still the thing to keep?
4. **Ports.** The exact number and mix for the 5-6 player board, and the rule for where Seafarers harbours may be. These have to come from the rulebooks.
5. **Language.** The cards on the sheet are in English today. Should the new cards (Cities & Knights costs, the barbarian track) also come in Hebrew, and how is the language chosen?
6. **Other expansions.** Traders & Barbarians, Explorers & Pirates and the scenario packs are out of this note. Is any of them wanted?
7. **How exact.** Should a board be checked for fairness (for example the sum of the dots around a start place), or only for the rules the tool has now?
8. **Rule sources.** The numbers marked **(check)** need the rulebooks (or the numbers on the physical boxes) in front of whoever builds this.

---

# The next batch (added 19 October)

**Status (19 October, later):** items 1, 2, 3 and 5 are **built** (flags `L` and `U`, bigger digits, the Hebrew card with `--lang`); item 6 is **built on the website** (`app/map_qr.py` in only-games; the library needed nothing); item 4 is **built**: three icon sets (`catan_map/icons.py`, compared in `docs/icons-comparison.svg`), **B, realistic, chosen as the default** (`--icons` picks another); items 7, 8 and 9 are built in only-games (see its `docs/tournament-maps-plan.md`, "As built"). What differs from the text below: the Hebrew points are written `[1 נק"נ]`; there is no reader warning for touching terrains (item 2); the QR picture is a single SVG with the logo inside, scanned with a real reader in the site's tests.

Nine items. Items 1 to 6 are about `catan-map` and its drawing and are described here; items 7 to 9 are about the OnlyGames site (tournaments, the open-table form, the phone) and are in `only-games/docs/tournament-maps-plan.md`, with a short note here where the library is involved. Each item says what it would change, a **default** where something has to be chosen, and what it needs to be checked. The numbers are the ones of the list that was given.

## 1. A flag and a checkbox for "2 and 12 may not touch" (default: on)

**Now:** the 2 and the 12 never touch, always, even with the `A` flag (which only allows touching 6 and 8). There is no way to turn this off.

**Change:** make it a choice that is **on by default**, so every board that exists keeps its string.

- **Seed code:** a flag for the case where touching is *allowed*, because only the non-default value is written (as `A` does for the 6 and 8). Suggested letter: `L` (low and high). It is a flag that changes the string, so it belongs in the seed code. Letters in use: `F E I C R A P`.
- **Command line:** `--allow-adjacent-2-12`, next to `--allow-adjacent-red`.
- **Website:** a checkbox "2 ו-12 לא צמודים", **ticked by default**; unticking it adds `L` to the seed code. When a seed code already says `L` the box shows unticked (and an option that contradicts the code is an error, as for the other flags).
- **Generator:** the retry loop in `_generate_tokens` stops testing `adjacent_low_high_pairs` when the flag is set. With the flag **off** (the default) nothing changes, so no golden test moves; one new golden case is added for `L`.
- **Reader:** touching 2 and 12 stays a warning, as now.

**Decision (default):** letter `L`; the rule stays **on** unless the flag is given.

## 2. A flag and a checkbox for "no two neighbouring tiles of the same type" (default: off)

**What it is:** a new rule: no two land tiles that touch may have the same terrain (no wood next to wood, and so on).

- **Seed code:** a flag that switches it **on** (default off, so nothing existing changes). Suggested letter: `U` (unlike neighbours).
- **Command line:** `--no-same-neighbours`.
- **Website:** a checkbox "בלי אריחים זהים צמודים", **unticked by default**; ticking it adds `U` to the code.
- **Generator:** the tiles are drawn first (desert, then the 18 resource tiles shuffled), so this rule goes in `_generate_tiles`: shuffle again until no two neighbours match, the way the tokens are reshuffled for the red numbers (same stream, at most `MAX_ATTEMPTS`). **Open point:** how often a random shuffle passes. With 4, 4, 4, 3, 3 tiles of the five terrains on 19 places it may be rare, so a shuffle-until-it-works loop could need thousands of tries or fail. This has to be **measured first**; if it is too slow, the generator places the terrains one by one, choosing at random among those that fit (still only using the stream, so it stays the same for a seed). The measuring was done: a random shuffle passes about 1 in 1,300 with the desert in the center and 1 in 4,000 on the edge, which is too rare for the retry loop; so the tiles are placed one by one (built, 0.1 ms a board, over a few thousand seeds every board passes).
- **Order of the stream:** the rule changes how many draws the tiles take, so the draws that follow (the tokens and the ports) change too, but only when the flag is on, which is a different seed code. A board without the flag is untouched.
- **Reader:** no warning for touching terrains: most ordinary boards have some, so a warning would be noise. The rule is for generating only.
- **Interaction with the desert zone:** none; the desert is one tile of its own type.

**Decision (default):** letter `U`; **off**.

## 3. Bigger digits on the tokens (the token keeps its size)

**Now:** the number is 26 units high for one digit and 23 for 10, 11, 12, on a token of radius 31, with the pips under it.

**Change:** about 30% larger digits (for example 34 and 29), the digits moved a little up and the pips kept below them, so that nothing touches the rim; the token stays 25 mm on the sheet. This changes every drawing, so it is a plain change of constants with a look at the result in the three tile sets, both on the screen image and on the sheet. No option is planned (a larger number is easier to read; nothing needs the old one), but one constant makes it easy to add if wanted.

**To check:** two-digit numbers (10, 11, 12) at the new size still fit inside the circle with room; the red 6 and 8 with five pips; the 2 and the 12 with one pip.

## 4. More detailed, more realistic resource icons (the sheep, and the "ship")

**Now:** the icons are small flat drawings used in the port badges, the costs cards and the bank slots: a pine, a sheep, a wheat ear, bricks, a pile of rocks.

**Point to settle: "the ship".** There is no ship in the tool today. It may mean the **sheep** (the icon that looks weakest), or the **ship** of Seafarers (section 5 of this note), which would be a new icon. The plan below does the five resources and the ship, so both readings are covered.

**What would be made:** a **comparison sheet** (one SVG, opened in the browser) with, for each icon, the **current** one next to two or three new ones, large and also at the real size they have on the sheet (about 10 mm on a card, 36 mm in a bank slot), on the light background and on the badge:

- **A: detailed flat**: the same look, with more shapes (sheep with a woolly body, legs, an ear and a face; a pine with branches; sheaf with grains and leaves; stacked bricks with mortar; rocks with facets and cracks);
- **B: realistic**: the painted look of the realistic tiles (gradients, shadow, texture);
- (maybe) **C: line art**, one colour, as on a printed rulebook.

The choice is yours; then the chosen set replaces the old icons in `svg_tiles.py` (and, as an option, the old set stays as `--icons simple`). Nothing else in the code changes: the icons are used by name.

**Default:** none until you choose.

## 5. The costs card in Hebrew (default) and in English, with a switch

**Now:** the card is in English (Building Costs, Road, Settlement, City, Development Card, `[1 VP]`).

**Change:** a language for the card, **Hebrew by default**.

- **Command line:** `--lang he|en` (default `he`). It applies to the texts of the `costs` element (and to anything else with words that is added later).
- **Python:** `render_svg(..., lang="he")`; the card texts are in one table per language, in one file, so a change of wording is one line.
- **Website:** a switch in the image settings, "שפת כרטיס העלויות: עברית / English", **Hebrew by default**.
- **Texts (to confirm):** title עלויות בנייה; דרך, יישוב, עיר, קלף התפתחות; the points as `[0 נק׳]`, `[1 נק׳]`, `[2 נק׳]`, `[? נק׳]` (or `נקודת ניצחון`).
- **Layout:** Hebrew reads from the right, so the card is mirrored: the name on the right, the chips on the left; the dash and the order of the words follow. The four turned cards keep their turns.
- **Fonts:** an SVG cannot carry a font, so the card says `Arial, "Noto Sans Hebrew", sans-serif`, which every system has a Hebrew face for; the serif face of the English card is kept for English. This should be looked at in Chrome, Firefox and Safari, and in the PNG and A4 PDF the website makes.
- **This changes every sheet that is made with `costs` and no `--lang`** (the default moves from English to Hebrew). That is intended; the tests that read the English texts get the language passed explicitly.

**Decision (default):** `he`; the Hebrew texts above, to be corrected by you.

## 6. A QR code from a URL, in the style of `logo_w_qr.png`, on top of the logo

**What it is:** type a web address and get a QR code in the style of the one in `logo_w_qr.png` (modules in a gradient from blue to magenta, rounded corner squares, the small OnlyGames logo in the middle), placed **above the logo** on the sheet, as in that picture.

- **Where it lives.** `catan-map` has no dependencies (standard library only); making a QR code needs an encoder. The website already has one (`segno`, used for the tournament QR). So the code that draws the QR belongs to **the website**, and `catan-map` only gets the finished picture as the `logo` (it already takes any image and fits it). An optional `catan-map[qr]` extra with `segno` could add `--qr URL` to the command line later; that is not needed for the website.
- **How it is drawn.** `segno` gives the matrix of modules. The picture is made from it as an **SVG**: the modules as squares (neighbours joined into paths, so the file is small), the three finder patterns as rounded squares, a vertical gradient fill (the two colours of the sample), the middle cleared for the logo, and the logo in a rounded light square there. The correction level must be the highest (H) so that the logo can hide part of the code.
- **The stack.** One picture: the QR on top, then the logo (the plain OnlyGames logo, which is the transparent `onlygames_logo.png`), the same stacking as `logo_w_qr.png`. Because it is an SVG with the logo inside, the sheet's fitting code reads its shape from the `viewBox` and fits it like any logo.
- **Website:** in the logo settings, a box "כתובת לקוד QR" (a URL). Empty means **no QR** and the plain logo. The old default (the fixed picture `logo_w_qr.png` with the OnlyGames QR) stays as one of the choices, or its address becomes the **default value of the box**, so the default sheet looks as it does now.
- **Safety.** Only `http://` and `https://` addresses, a length limit, no spaces; the text is only encoded, never opened by the server.
- **To check (important): the code must scan.** The gradient and the logo reduce contrast and area. The test renders the picture and **decodes it with a reader** (if one is available in the test environment, such as OpenCV's `QRCodeDetector` or `zbarimg`), and a phone is the last test on a printed sheet. The size on the sheet (the logo box, about 95 x 70 mm) puts a limit on the module size: a long URL makes a dense code that is small to scan at that size, so the page should show the length and warn when it is long (a short link is better).

**Decision (default):** the box is **empty by default**; the stack QR + logo is made only when a URL is given.

## 7, 8, 9. Maps on tournaments, the open-table form, and the phone

These are website work and are planned in `only-games/docs/tournament-maps-plan.md`. For the library they ask for nothing new: the open-table form uses the same `make()` and `render_svg()` calls as the generator page.

## Order, and what depends on what

| Step | Items | Why in this order |
|---|---|---|
| A | 3, 1, 5 | small, and change what every drawing looks like; best done together so the tests and the pictures change once |
| B | 2 | needs a measurement first; touches the generator and the seed code |
| C | 4 | needs your choice from the comparison sheet |
| D | 6 | website; after the logo handling is final |
| E | 7, 8, 9 | website; item 7 first (the data), then 8 (the form), then 9 (the phone pass over all the new pages) |

## Questions for you

1. **Letters** `L` and `U` for items 1 and 2: right, or others?
2. **Item 4:** is "the ship" the sheep, the Seafarers ship, or both?
3. **Item 5:** the Hebrew texts, `נק׳` or `נקודת ניצחון`? Should the language switch also apply to the **bank** and other texts if they get words later?
4. **Item 6:** the default of the QR box: empty, or `https://onlygames.co.il`?
5. **Item 3:** one size for the digits, or a setting for small and large?
