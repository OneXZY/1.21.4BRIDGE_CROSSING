"""
Quad (2x2) Crossing Detector Module
Detects 2x2 arranged crossings in Nether Fortress
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from fortress_generator import StructurePiece, PieceType, BoundingBox


@dataclass
class QuadCrossing:
    """Quad crossing (2x2 arrangement)"""
    crossings: List[StructurePiece]
    center: Tuple[int, int, int]
    bounding_box: BoundingBox

    def __str__(self):
        return (f"Quad Crossing:\n"
                f"  Center: X={self.center[0]}, Y={self.center[1]}, Z={self.center[2]}\n"
                f"  Bounds: ({self.bounding_box.min_x}, {self.bounding_box.min_z}) -> "
                f"({self.bounding_box.max_x}, {self.bounding_box.max_z})")


class CrossingDetector:
    """Crossing detector"""

    # BridgeCrossing size is 19x10x19
    CROSSING_SIZE = 19

    def __init__(self, crossings: List[StructurePiece]):
        """
        Initialize detector

        Args:
            crossings: List of crossing pieces
        """
        self.crossings = crossings

    def find_quad_crossings(self) -> List[QuadCrossing]:
        """
        Find all quad (2x2) crossings

        A quad crossing is 4 crossings arranged in a 2x2 pattern,
        with adjacent or overlapping bounding boxes forming a larger cross area.

        Returns:
            List of quad crossings
        """
        quad_crossings = []

        if len(self.crossings) < 4:
            return quad_crossings

        # Get center coordinates of all crossings
        crossing_centers = []
        for crossing in self.crossings:
            center = crossing.get_center()
            crossing_centers.append((center, crossing))

        # Check if each crossing can be the top-left corner of a 2x2
        for i, (center1, crossing1) in enumerate(crossing_centers):
            # Find possible 2x2 combinations
            quad = self._find_quad_from_corner(crossing1, crossing_centers)
            if quad and not self._is_duplicate_quad(quad, quad_crossings):
                quad_crossings.append(quad)

        return quad_crossings

    def _find_quad_from_corner(self, corner_crossing: StructurePiece,
                                all_crossings: List[Tuple[Tuple[int, int, int], StructurePiece]]) -> Optional[QuadCrossing]:
        """
        Find 2x2 combination starting from a corner crossing.

        For a TRUE quad crossing, all 4 crossings must be DIRECTLY adjacent,
        forming a large square with no bridges in between.

        Args:
            corner_crossing: Corner crossing
            all_crossings: All crossings with their center coordinates

        Returns:
            Found quad crossing, or None if not found
        """
        corner_center = corner_crossing.get_center()
        corner_box = corner_crossing.bounding_box

        neighbors = {
            'right': None,  # +X direction (directly adjacent)
            'down': None,   # +Z direction (directly adjacent)
            'diagonal': None  # +X+Z direction
        }

        for center, crossing in all_crossings:
            if crossing == corner_crossing:
                continue

            dx = center[0] - corner_center[0]
            dz = center[2] - corner_center[2]

            # Check if DIRECTLY adjacent right neighbor (+X direction)
            if dx > 0 and self._is_directly_adjacent_x(corner_box, crossing.bounding_box):
                if neighbors['right'] is None or dx < (neighbors['right'].get_center()[0] - corner_center[0]):
                    neighbors['right'] = crossing

            # Check if DIRECTLY adjacent bottom neighbor (+Z direction)
            if dz > 0 and self._is_directly_adjacent_z(corner_box, crossing.bounding_box):
                if neighbors['down'] is None or dz < (neighbors['down'].get_center()[2] - corner_center[2]):
                    neighbors['down'] = crossing

        # If found right and bottom neighbors, find diagonal neighbor
        if neighbors['right'] and neighbors['down']:
            right_box = neighbors['right'].bounding_box
            down_box = neighbors['down'].bounding_box

            for center, crossing in all_crossings:
                if crossing in [corner_crossing, neighbors['right'], neighbors['down']]:
                    continue

                # Diagonal neighbor must be DIRECTLY adjacent to both right and bottom neighbors
                if (self._is_directly_adjacent_z(right_box, crossing.bounding_box) and
                    self._is_directly_adjacent_x(down_box, crossing.bounding_box)):
                    neighbors['diagonal'] = crossing
                    break

        # Check if found complete 2x2
        if all(neighbors.values()):
            crossings = [corner_crossing, neighbors['right'],
                        neighbors['down'], neighbors['diagonal']]

            # Calculate overall bounding box
            min_x = min(c.bounding_box.min_x for c in crossings)
            min_y = min(c.bounding_box.min_y for c in crossings)
            min_z = min(c.bounding_box.min_z for c in crossings)
            max_x = max(c.bounding_box.max_x for c in crossings)
            max_y = max(c.bounding_box.max_y for c in crossings)
            max_z = max(c.bounding_box.max_z for c in crossings)

            overall_box = BoundingBox(min_x, min_y, min_z, max_x, max_y, max_z)
            center = ((min_x + max_x) // 2, (min_y + max_y) // 2, (min_z + max_z) // 2)

            return QuadCrossing(crossings, center, overall_box)

        return None

    def _is_directly_adjacent_x(self, box1: BoundingBox, box2: BoundingBox) -> bool:
        """
        Check if two bounding boxes are DIRECTLY adjacent and ALIGNED in X direction.

        For true 2x2 quad crossings:
        - Z ranges must be EXACTLY the same (perfectly aligned)
        - Y ranges must be EXACTLY the same (same height)
        - Boxes must be directly touching (gap = 1)
        """
        # Z ranges must be EXACTLY the same (perfectly aligned)
        if box1.min_z != box2.min_z or box1.max_z != box2.max_z:
            return False

        # Y ranges must be EXACTLY the same (same height)
        if box1.min_y != box2.min_y or box1.max_y != box2.max_y:
            return False

        # Must be directly adjacent in X direction (gap = 1, touching)
        # box2 is to the right of box1
        if box2.min_x == box1.max_x + 1:
            return True
        # box1 is to the right of box2
        if box1.min_x == box2.max_x + 1:
            return True

        return False

    def _is_directly_adjacent_z(self, box1: BoundingBox, box2: BoundingBox) -> bool:
        """
        Check if two bounding boxes are DIRECTLY adjacent and ALIGNED in Z direction.

        For true 2x2 quad crossings:
        - X ranges must be EXACTLY the same (perfectly aligned)
        - Y ranges must be EXACTLY the same (same height)
        - Boxes must be directly touching (gap = 1)
        """
        # X ranges must be EXACTLY the same (perfectly aligned)
        if box1.min_x != box2.min_x or box1.max_x != box2.max_x:
            return False

        # Y ranges must be EXACTLY the same (same height)
        if box1.min_y != box2.min_y or box1.max_y != box2.max_y:
            return False

        # Must be directly adjacent in Z direction (gap = 1, touching)
        # box2 is below box1 (higher Z)
        if box2.min_z == box1.max_z + 1:
            return True
        # box1 is below box2
        if box1.min_z == box2.max_z + 1:
            return True

        return False

    def _is_adjacent_x(self, box1: BoundingBox, box2: BoundingBox) -> bool:
        """Check if two bounding boxes are adjacent in X direction (for connectivity)"""
        z_overlap = (box1.min_z <= box2.max_z and box1.max_z >= box2.min_z)
        if not z_overlap:
            return False
        gap = min(abs(box1.max_x - box2.min_x), abs(box2.max_x - box1.min_x))
        return gap <= 25

    def _is_adjacent_z(self, box1: BoundingBox, box2: BoundingBox) -> bool:
        """Check if two bounding boxes are adjacent in Z direction (for connectivity)"""
        x_overlap = (box1.min_x <= box2.max_x and box1.max_x >= box2.min_x)
        if not x_overlap:
            return False
        gap = min(abs(box1.max_z - box2.min_z), abs(box2.max_z - box1.min_z))
        return gap <= 25

    def _is_duplicate_quad(self, quad: QuadCrossing, existing: List[QuadCrossing]) -> bool:
        """Check if this is a duplicate quad crossing"""
        for existing_quad in existing:
            # Check if contains same crossings
            existing_set = set(id(c) for c in existing_quad.crossings)
            new_set = set(id(c) for c in quad.crossings)
            if existing_set == new_set:
                return True
        return False

    def find_connected_crossings(self) -> List[List[StructurePiece]]:
        """
        Find all connected crossing groups

        Returns:
            List of connected crossing groups
        """
        if not self.crossings:
            return []

        visited = set()
        groups = []

        for crossing in self.crossings:
            if id(crossing) in visited:
                continue

            group = []
            self._dfs_connected(crossing, visited, group)
            if len(group) >= 2:
                groups.append(group)

        return groups

    def _dfs_connected(self, crossing: StructurePiece, visited: set,
                       group: List[StructurePiece]):
        """DFS to find connected crossings"""
        if id(crossing) in visited:
            return

        visited.add(id(crossing))
        group.append(crossing)

        for other in self.crossings:
            if id(other) in visited:
                continue

            if self._are_connected(crossing, other):
                self._dfs_connected(other, visited, group)

    def _are_connected(self, c1: StructurePiece, c2: StructurePiece) -> bool:
        """Check if two crossings are connected"""
        return (self._is_adjacent_x(c1.bounding_box, c2.bounding_box) or
                self._is_adjacent_z(c1.bounding_box, c2.bounding_box))


def analyze_fortress_crossings(crossings: List[StructurePiece]) -> dict:
    """
    Analyze fortress crossings

    Args:
        crossings: List of crossings

    Returns:
        Analysis result dictionary
    """
    detector = CrossingDetector(crossings)

    quad_crossings = detector.find_quad_crossings()
    connected_groups = detector.find_connected_crossings()

    return {
        'total_crossings': len(crossings),
        'quad_crossings': quad_crossings,
        'connected_groups': connected_groups,
        'has_quad': len(quad_crossings) > 0
    }