import unittest

from catan_map import board as b


class Geometry(unittest.TestCase):
    def test_nineteen_tiles_in_five_rows(self):
        self.assertEqual(b.ROWS, (3, 4, 5, 4, 3))
        self.assertEqual(b.TILE_COUNT, 19)
        self.assertEqual(len(b.TILE_POSITIONS), 19)

    def test_neighbours_are_symmetric_and_have_the_right_sizes(self):
        for i, neighbours in enumerate(b.NEIGHBOURS):
            for j in neighbours:
                self.assertIn(i, b.NEIGHBOURS[j])
        sizes = sorted(len(n) for n in b.NEIGHBOURS)
        # 6 corners touch 3 tiles, 6 edge-middle tiles touch 4, the 6 around the centre touch 5... and
        # the centre touches 6 (every other tile touches the sea or is next to the centre)
        self.assertEqual(len(b.NEIGHBOURS[b.CENTER_TILE]), 6)
        self.assertEqual(sizes.count(3), 6)
        self.assertEqual(sum(sizes) // 2, 42)   # 42 shared edges between the 19 tiles

    def test_known_neighbours(self):
        self.assertEqual(sorted(b.NEIGHBOURS[0]), [1, 3, 4])
        self.assertEqual(sorted(b.NEIGHBOURS[9]), [4, 5, 8, 10, 13, 14])


class Zones(unittest.TestCase):
    def test_edge_inner_center_ring(self):
        self.assertEqual(sorted(b.EDGE_TILES), [0, 1, 2, 3, 6, 7, 11, 12, 15, 16, 17, 18])
        self.assertEqual(sorted(b.INNER_TILES), [4, 5, 8, 9, 10, 13, 14])
        self.assertEqual(sorted(b.CENTER_TILES), [9])
        self.assertEqual(sorted(b.RING_TILES), [4, 5, 8, 10, 13, 14])
        self.assertEqual(b.RING_TILES | b.CENTER_TILES, b.INNER_TILES)
        self.assertFalse(b.EDGE_TILES & b.INNER_TILES)

    def test_edge_tiles_are_the_ones_with_fewer_than_six_neighbours_that_touch_the_sea(self):
        # a tile touches the sea exactly when it has a free side: fewer than 6 neighbours
        for tile in range(19):
            self.assertEqual(tile in b.EDGE_TILES, len(b.NEIGHBOURS[tile]) < 6, tile)

    def test_the_desert_zones(self):
        sizes = {name: len(zone) for name, zone in b.DESERT_ZONES.items()}
        self.assertEqual(sizes, {"free": 19, "edge": 12, "inner": 7, "center": 1, "ring": 6})


class SeaRing(unittest.TestCase):
    def test_the_table_matches_the_coordinates(self):
        for position, (row, x) in enumerate(b.RING_POSITIONS):
            real = sorted(
                i for i, tile in enumerate(b.TILE_POSITIONS) if b._touch((row, x), tile)
            )
            self.assertEqual(sorted(b.RING_TOUCHES[position]), real, position)

    def test_each_island_tile_lies_in_exactly_one_direction_from_the_sea_tiles_it_touches(self):
        for position, touches in enumerate(b.RING_TOUCHES):
            for tile in touches:
                self.assertIn(b.direction(position, tile), {"E", "W", "NE", "NW", "SE", "SW"})

    def test_the_order_is_clockwise_so_that_neighbours_share_a_tile(self):
        for position in range(b.RING_SIZE):
            following = (position + 1) % b.RING_SIZE
            self.assertEqual(b.RING_TOUCHES[position][-1], b.RING_TOUCHES[following][0], position)

    def test_thirty_coast_edges_and_six_corners(self):
        self.assertEqual(sum(len(t) for t in b.RING_TOUCHES), 30)
        self.assertEqual(b.CORNER_POSITIONS, (0, 3, 6, 9, 12, 15))


class PortSlots(unittest.TestCase):
    def test_positions_without_and_with_the_shift(self):
        self.assertEqual([b.port_ring_position(k, False) for k in range(9)], list(range(0, 18, 2)))
        self.assertEqual([b.port_ring_position(k, True) for k in range(9)], list(range(1, 18, 2)))

    def test_corner_slots(self):
        self.assertEqual([k for k in range(9) if b.is_corner_slot(k, False)], [0, 3, 6])
        self.assertEqual([k for k in range(9) if b.is_corner_slot(k, True)], [1, 4, 7])

    def test_the_target_tile_of_a_port(self):
        # ring 2 touches tiles 1 and 2: backward -> 1, forward -> 2
        self.assertEqual(b.port_target_tile(1, False, False), 1)
        self.assertEqual(b.port_target_tile(1, False, True), 2)
        # a corner has only one tile whatever the orientation
        self.assertEqual(b.port_target_tile(0, False, False), 0)
        self.assertEqual(b.port_target_tile(0, False, True), 0)

    def test_the_default_ports_have_the_right_pieces(self):
        kinds = [("3" if c in "3#" else c.upper()) for c in b.DEFAULT_PORTS]
        self.assertEqual(sorted(kinds), sorted("3333WOCSG"))


class RedNumbers(unittest.TestCase):
    def test_adjacent_red_pairs(self):
        tokens = [None] * 19
        tokens[0], tokens[1], tokens[4], tokens[18] = "6", "8", "6", "8"
        # tiles 0, 1 and 4 all touch each other
        self.assertEqual(b.adjacent_red_pairs(tokens), [(0, 1), (0, 4), (1, 4)])
        tokens[1] = "5"
        self.assertEqual(b.adjacent_red_pairs(tokens), [(0, 4)])

    def test_none_when_the_reds_are_apart(self):
        tokens = [None] * 19
        tokens[0], tokens[18] = "6", "8"
        self.assertEqual(b.adjacent_red_pairs(tokens), [])


if __name__ == "__main__":
    unittest.main()
