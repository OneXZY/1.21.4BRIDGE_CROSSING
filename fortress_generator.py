# -*- coding: utf-8 -*-
"""
Nether Fortress Structure Generation Simulation Module
Based on Minecraft 1.21.4 NetherFortressPieces algorithm
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Tuple
from random_source import WorldgenRandom, get_random_horizontal_direction


class Direction(Enum):
    """Direction enum"""
    NORTH = 0  # -Z
    EAST = 1   # +X
    SOUTH = 2  # +Z
    WEST = 3   # -X


class PieceType(Enum):
    """Structure piece type"""
    # Bridge parts
    BRIDGE_STRAIGHT = "BridgeStraight"
    BRIDGE_CROSSING = "BridgeCrossing"  # Crossroad
    ROOM_CROSSING = "RoomCrossing"
    STAIRS_ROOM = "StairsRoom"
    MONSTER_THRONE = "MonsterThrone"
    CASTLE_ENTRANCE = "CastleEntrance"
    BRIDGE_END_FILLER = "BridgeEndFiller"

    # Castle parts
    CASTLE_SMALL_CORRIDOR = "CastleSmallCorridorPiece"
    CASTLE_SMALL_CORRIDOR_CROSSING = "CastleSmallCorridorCrossingPiece"
    CASTLE_SMALL_CORRIDOR_RIGHT_TURN = "CastleSmallCorridorRightTurnPiece"
    CASTLE_SMALL_CORRIDOR_LEFT_TURN = "CastleSmallCorridorLeftTurnPiece"
    CASTLE_CORRIDOR_STAIRS = "CastleCorridorStairsPiece"
    CASTLE_CORRIDOR_T_BALCONY = "CastleCorridorTBalconyPiece"
    CASTLE_STALK_ROOM = "CastleStalkRoom"

    START_PIECE = "StartPiece"


@dataclass
class BoundingBox:
    """Bounding box"""
    min_x: int
    min_y: int
    min_z: int
    max_x: int
    max_y: int
    max_z: int

    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if two bounding boxes intersect"""
        return (self.max_x >= other.min_x and self.min_x <= other.max_x and
                self.max_z >= other.min_z and self.min_z <= other.max_z and
                self.max_y >= other.min_y and self.min_y <= other.max_y)

    @staticmethod
    def orient_box(x: int, y: int, z: int, offset_x: int, offset_y: int, offset_z: int,
                   width: int, height: int, depth: int, direction: Direction) -> 'BoundingBox':
        """Create oriented bounding box based on direction (used by createPiece methods)"""
        if direction == Direction.NORTH:
            return BoundingBox(
                x + offset_x, y + offset_y, z - depth + 1 + offset_z,
                x + width - 1 + offset_x, y + height - 1 + offset_y, z + offset_z
            )
        elif direction == Direction.SOUTH:
            return BoundingBox(
                x + offset_x, y + offset_y, z + offset_z,
                x + width - 1 + offset_x, y + height - 1 + offset_y, z + depth - 1 + offset_z
            )
        elif direction == Direction.WEST:
            return BoundingBox(
                x - depth + 1 + offset_z, y + offset_y, z + offset_x,
                x + offset_z, y + height - 1 + offset_y, z + width - 1 + offset_x
            )
        else:  # EAST
            return BoundingBox(
                x + offset_z, y + offset_y, z + offset_x,
                x + depth - 1 + offset_z, y + height - 1 + offset_y, z + width - 1 + offset_x
            )

    @staticmethod
    def make_bounding_box(x: int, y: int, z: int, direction: Direction,
                          width: int, height: int, depth: int) -> 'BoundingBox':
        """Create bounding box for StartPiece (used by StructurePiece.makeBoundingBox in Java)

        This is different from orient_box! Used only for StartPiece initialization.
        """
        # direction.getAxis() == Direction.Axis.Z means NORTH or SOUTH
        if direction in [Direction.NORTH, Direction.SOUTH]:
            return BoundingBox(x, y, z, x + width - 1, y + height - 1, z + depth - 1)
        else:  # EAST or WEST (axis == X)
            return BoundingBox(x, y, z, x + depth - 1, y + height - 1, z + width - 1)


@dataclass
class PieceWeight:
    """Piece weight"""
    piece_type: PieceType
    weight: int
    max_place_count: int
    allow_in_row: bool = False
    place_count: int = 0

    def do_place(self, depth: int) -> bool:
        return self.max_place_count == 0 or self.place_count < self.max_place_count

    def is_valid(self) -> bool:
        return self.max_place_count == 0 or self.place_count < self.max_place_count


@dataclass
class StructurePiece:
    """Structure piece"""
    piece_type: PieceType
    bounding_box: BoundingBox
    direction: Direction
    gen_depth: int

    def get_center(self) -> Tuple[int, int, int]:
        """Get center coordinates"""
        return (
            (self.bounding_box.min_x + self.bounding_box.max_x) // 2,
            (self.bounding_box.min_y + self.bounding_box.max_y) // 2,
            (self.bounding_box.min_z + self.bounding_box.max_z) // 2
        )


class FortressGenerator:
    """Nether Fortress Generator"""

    MAX_DEPTH = 30
    LOWEST_Y_POSITION = 10
    MAGIC_START_Y = 64

    # Bridge piece weights
    BRIDGE_PIECE_WEIGHTS = [
        PieceWeight(PieceType.BRIDGE_STRAIGHT, 30, 0, True),
        PieceWeight(PieceType.BRIDGE_CROSSING, 10, 4),
        PieceWeight(PieceType.ROOM_CROSSING, 10, 4),
        PieceWeight(PieceType.STAIRS_ROOM, 10, 3),
        PieceWeight(PieceType.MONSTER_THRONE, 5, 2),
        PieceWeight(PieceType.CASTLE_ENTRANCE, 5, 1),
    ]

    # Castle piece weights
    CASTLE_PIECE_WEIGHTS = [
        PieceWeight(PieceType.CASTLE_SMALL_CORRIDOR, 25, 0, True),
        PieceWeight(PieceType.CASTLE_SMALL_CORRIDOR_CROSSING, 15, 5),
        PieceWeight(PieceType.CASTLE_SMALL_CORRIDOR_RIGHT_TURN, 5, 10),
        PieceWeight(PieceType.CASTLE_SMALL_CORRIDOR_LEFT_TURN, 5, 10),
        PieceWeight(PieceType.CASTLE_CORRIDOR_STAIRS, 10, 3, True),
        PieceWeight(PieceType.CASTLE_CORRIDOR_T_BALCONY, 7, 2),
        PieceWeight(PieceType.CASTLE_STALK_ROOM, 5, 2),
    ]

    # Piece dimensions (width, height, depth)
    PIECE_DIMENSIONS = {
        PieceType.BRIDGE_STRAIGHT: (5, 10, 19),
        PieceType.BRIDGE_CROSSING: (19, 10, 19),
        PieceType.ROOM_CROSSING: (7, 9, 7),
        PieceType.STAIRS_ROOM: (7, 11, 7),
        PieceType.MONSTER_THRONE: (7, 8, 9),
        PieceType.CASTLE_ENTRANCE: (13, 14, 13),
        PieceType.BRIDGE_END_FILLER: (5, 10, 8),
        PieceType.CASTLE_SMALL_CORRIDOR: (5, 7, 5),
        PieceType.CASTLE_SMALL_CORRIDOR_CROSSING: (5, 7, 5),
        PieceType.CASTLE_SMALL_CORRIDOR_RIGHT_TURN: (5, 7, 5),
        PieceType.CASTLE_SMALL_CORRIDOR_LEFT_TURN: (5, 7, 5),
        PieceType.CASTLE_CORRIDOR_STAIRS: (5, 14, 10),
        PieceType.CASTLE_CORRIDOR_T_BALCONY: (9, 7, 9),
        PieceType.CASTLE_STALK_ROOM: (13, 14, 13),
        PieceType.START_PIECE: (19, 10, 19),
    }

    # Piece bounding box offsets (offset_x, offset_y, offset_z)
    PIECE_OFFSETS = {
        PieceType.BRIDGE_STRAIGHT: (-1, -3, 0),
        PieceType.BRIDGE_CROSSING: (-8, -3, 0),
        PieceType.ROOM_CROSSING: (-2, 0, 0),
        PieceType.STAIRS_ROOM: (-2, 0, 0),
        PieceType.MONSTER_THRONE: (-2, 0, 0),
        PieceType.CASTLE_ENTRANCE: (-5, -3, 0),
        PieceType.BRIDGE_END_FILLER: (-1, -3, 0),
        PieceType.CASTLE_SMALL_CORRIDOR: (-1, 0, 0),
        PieceType.CASTLE_SMALL_CORRIDOR_CROSSING: (-1, 0, 0),
        PieceType.CASTLE_SMALL_CORRIDOR_RIGHT_TURN: (-1, 0, 0),
        PieceType.CASTLE_SMALL_CORRIDOR_LEFT_TURN: (-1, 0, 0),
        PieceType.CASTLE_CORRIDOR_STAIRS: (-1, -7, 0),
        PieceType.CASTLE_CORRIDOR_T_BALCONY: (-3, 0, 0),
        PieceType.CASTLE_STALK_ROOM: (-5, -3, 0),
        PieceType.START_PIECE: (-8, -3, 0),
    }

    def __init__(self, world_seed: int, chunk_x: int, chunk_z: int):
        self.world_seed = world_seed
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.random = WorldgenRandom(0)
        self.pieces: List[StructurePiece] = []
        self.pending_children: List[StructurePiece] = []

        # Reset weight counts
        self.bridge_weights = [
            PieceWeight(pw.piece_type, pw.weight, pw.max_place_count, pw.allow_in_row)
            for pw in self.BRIDGE_PIECE_WEIGHTS
        ]
        self.castle_weights = [
            PieceWeight(pw.piece_type, pw.weight, pw.max_place_count, pw.allow_in_row)
            for pw in self.CASTLE_PIECE_WEIGHTS
        ]
        self.previous_piece: Optional[PieceWeight] = None
        self.start_bounding_box: Optional[BoundingBox] = None

    def _set_structure_seed(self):
        """Set structure generation random seed

        Based on Structure.GenerationContext.makeRandom() in Java:
        WorldgenRandom worldgenRandom = new WorldgenRandom(new LegacyRandomSource(0L));
        worldgenRandom.setLargeFeatureSeed(l, chunkPos.x, chunkPos.z);
        """
        self.random.set_large_feature_seed(self.world_seed, self.chunk_x, self.chunk_z)

    def generate(self) -> List[StructurePiece]:
        """Generate fortress structure"""
        self._set_structure_seed()

        # Create start piece (StartPiece, which is a BridgeCrossing)
        # Java: new StartPiece(random, chunkPos.getBlockX(2), chunkPos.getBlockZ(2))
        start_x = self.chunk_x * 16 + 2
        start_z = self.chunk_z * 16 + 2
        start_direction = Direction(get_random_horizontal_direction(self.random))

        # IMPORTANT: StartPiece uses makeBoundingBox, NOT orientBox!
        # Java: StructurePiece.makeBoundingBox(i, 64, j, direction, 19, 10, 19)
        start_box = BoundingBox.make_bounding_box(
            start_x, self.MAGIC_START_Y, start_z,
            start_direction, 19, 10, 19
        )

        start_piece = StructurePiece(
            PieceType.START_PIECE,
            start_box,
            start_direction,
            0
        )

        self.pieces.append(start_piece)
        self.start_bounding_box = start_box

        # Add children for start piece
        self._add_children_for_crossing(start_piece)

        # Process pending children
        while self.pending_children:
            idx = self.random.next_int(len(self.pending_children))
            piece = self.pending_children.pop(idx)
            self._add_children(piece)

        return self.pieces

    def _add_children(self, piece: StructurePiece):
        """Add children for piece"""
        if piece.piece_type in [PieceType.START_PIECE, PieceType.BRIDGE_CROSSING]:
            self._add_children_for_crossing(piece)
        elif piece.piece_type == PieceType.BRIDGE_STRAIGHT:
            self._add_children_for_bridge_straight(piece)
        elif piece.piece_type == PieceType.ROOM_CROSSING:
            self._add_children_for_room_crossing(piece)
        elif piece.piece_type == PieceType.STAIRS_ROOM:
            self._add_children_for_stairs_room(piece)
        elif piece.piece_type == PieceType.CASTLE_ENTRANCE:
            self._add_children_for_castle_entrance(piece)
        elif piece.piece_type == PieceType.CASTLE_SMALL_CORRIDOR:
            self._add_children_for_castle_small_corridor(piece)
        elif piece.piece_type == PieceType.CASTLE_SMALL_CORRIDOR_CROSSING:
            self._add_children_for_castle_small_corridor_crossing(piece)
        elif piece.piece_type == PieceType.CASTLE_SMALL_CORRIDOR_RIGHT_TURN:
            self._add_children_for_castle_right_turn(piece)
        elif piece.piece_type == PieceType.CASTLE_SMALL_CORRIDOR_LEFT_TURN:
            self._add_children_for_castle_left_turn(piece)
        elif piece.piece_type == PieceType.CASTLE_CORRIDOR_STAIRS:
            self._add_children_for_castle_corridor_stairs(piece)
        elif piece.piece_type == PieceType.CASTLE_CORRIDOR_T_BALCONY:
            self._add_children_for_castle_t_balcony(piece)
        elif piece.piece_type == PieceType.CASTLE_STALK_ROOM:
            self._add_children_for_castle_stalk_room(piece)

    def _add_children_for_crossing(self, piece: StructurePiece):
        """BridgeCrossing children generation"""
        self._generate_child_forward(piece, 8, 3, False)
        self._generate_child_left(piece, 3, 8, False)
        self._generate_child_right(piece, 3, 8, False)

    def _add_children_for_bridge_straight(self, piece: StructurePiece):
        """BridgeStraight children generation"""
        self._generate_child_forward(piece, 1, 3, False)

    def _add_children_for_room_crossing(self, piece: StructurePiece):
        """RoomCrossing children generation"""
        self._generate_child_forward(piece, 2, 0, False)
        self._generate_child_left(piece, 0, 2, False)
        self._generate_child_right(piece, 0, 2, False)

    def _add_children_for_stairs_room(self, piece: StructurePiece):
        """StairsRoom children generation"""
        self._generate_child_right(piece, 6, 2, False)

    def _add_children_for_castle_entrance(self, piece: StructurePiece):
        """CastleEntrance children generation"""
        self._generate_child_forward(piece, 5, 3, True)

    def _add_children_for_castle_small_corridor(self, piece: StructurePiece):
        """CastleSmallCorridorPiece children generation"""
        self._generate_child_forward(piece, 1, 0, True)

    def _add_children_for_castle_small_corridor_crossing(self, piece: StructurePiece):
        """CastleSmallCorridorCrossingPiece children generation"""
        self._generate_child_forward(piece, 1, 0, True)
        self._generate_child_left(piece, 0, 1, True)
        self._generate_child_right(piece, 0, 1, True)

    def _add_children_for_castle_right_turn(self, piece: StructurePiece):
        """CastleSmallCorridorRightTurnPiece children generation"""
        self._generate_child_right(piece, 0, 1, True)

    def _add_children_for_castle_left_turn(self, piece: StructurePiece):
        """CastleSmallCorridorLeftTurnPiece children generation"""
        self._generate_child_left(piece, 0, 1, True)

    def _add_children_for_castle_corridor_stairs(self, piece: StructurePiece):
        """CastleCorridorStairsPiece children generation"""
        self._generate_child_forward(piece, 1, 0, True)

    def _add_children_for_castle_t_balcony(self, piece: StructurePiece):
        """CastleCorridorTBalconyPiece children generation"""
        direction = piece.direction
        if direction == Direction.WEST or direction == Direction.NORTH:
            i = 5
        else:
            i = 1

        self._generate_child_left(piece, 0, i, self.random.next_int(8) > 0)
        self._generate_child_right(piece, 0, i, self.random.next_int(8) > 0)

    def _add_children_for_castle_stalk_room(self, piece: StructurePiece):
        """CastleStalkRoom children generation"""
        self._generate_child_forward(piece, 5, 3, True)
        self._generate_child_forward(piece, 5, 11, True)

    def _generate_child_forward(self, piece: StructurePiece, offset_i: int, offset_j: int, is_castle: bool):
        """Generate child forward"""
        direction = piece.direction
        box = piece.bounding_box

        if direction == Direction.NORTH:
            x = box.min_x + offset_i
            y = box.min_y + offset_j
            z = box.min_z - 1
        elif direction == Direction.SOUTH:
            x = box.min_x + offset_i
            y = box.min_y + offset_j
            z = box.max_z + 1
        elif direction == Direction.WEST:
            x = box.min_x - 1
            y = box.min_y + offset_j
            z = box.min_z + offset_i
        else:  # EAST
            x = box.max_x + 1
            y = box.min_y + offset_j
            z = box.min_z + offset_i

        self._generate_and_add_piece(x, y, z, direction, piece.gen_depth, is_castle)

    def _generate_child_left(self, piece: StructurePiece, offset_i: int, offset_j: int, is_castle: bool):
        """Generate child left"""
        direction = piece.direction
        box = piece.bounding_box

        if direction == Direction.NORTH:
            x = box.min_x - 1
            y = box.min_y + offset_i
            z = box.min_z + offset_j
            new_direction = Direction.WEST
        elif direction == Direction.SOUTH:
            x = box.min_x - 1
            y = box.min_y + offset_i
            z = box.min_z + offset_j
            new_direction = Direction.WEST
        elif direction == Direction.WEST:
            x = box.min_x + offset_j
            y = box.min_y + offset_i
            z = box.min_z - 1
            new_direction = Direction.NORTH
        else:  # EAST
            x = box.min_x + offset_j
            y = box.min_y + offset_i
            z = box.min_z - 1
            new_direction = Direction.NORTH

        self._generate_and_add_piece(x, y, z, new_direction, piece.gen_depth, is_castle)

    def _generate_child_right(self, piece: StructurePiece, offset_i: int, offset_j: int, is_castle: bool):
        """Generate child right"""
        direction = piece.direction
        box = piece.bounding_box

        if direction == Direction.NORTH:
            x = box.max_x + 1
            y = box.min_y + offset_i
            z = box.min_z + offset_j
            new_direction = Direction.EAST
        elif direction == Direction.SOUTH:
            x = box.max_x + 1
            y = box.min_y + offset_i
            z = box.min_z + offset_j
            new_direction = Direction.EAST
        elif direction == Direction.WEST:
            x = box.min_x + offset_j
            y = box.min_y + offset_i
            z = box.max_z + 1
            new_direction = Direction.SOUTH
        else:  # EAST
            x = box.min_x + offset_j
            y = box.min_y + offset_i
            z = box.max_z + 1
            new_direction = Direction.SOUTH

        self._generate_and_add_piece(x, y, z, new_direction, piece.gen_depth, is_castle)

    def _generate_and_add_piece(self, x: int, y: int, z: int, direction: Direction,
                                 depth: int, is_castle: bool):
        """Generate and add piece"""
        # Check distance limit
        if self.start_bounding_box:
            if abs(x - self.start_bounding_box.min_x) > 112:
                return None
            if abs(z - self.start_bounding_box.min_z) > 112:
                return None

        weights = self.castle_weights if is_castle else self.bridge_weights
        piece = self._generate_piece(weights, x, y, z, direction, depth + 1)

        if piece:
            self.pieces.append(piece)
            self.pending_children.append(piece)

        return piece

    def _generate_piece(self, weights: List[PieceWeight], x: int, y: int, z: int,
                        direction: Direction, depth: int) -> Optional[StructurePiece]:
        """Generate piece based on weights"""
        total_weight = self._update_piece_weight(weights)
        can_place = total_weight > 0 and depth <= self.MAX_DEPTH

        attempts = 0
        while attempts < 5 and can_place:
            attempts += 1
            target = self.random.next_int(total_weight)

            for pw in weights:
                target -= pw.weight
                if target < 0:
                    if not pw.do_place(depth):
                        break
                    if pw == self.previous_piece and not pw.allow_in_row:
                        break

                    piece = self._create_piece(pw.piece_type, x, y, z, direction, depth)
                    if piece:
                        pw.place_count += 1
                        self.previous_piece = pw
                        if not pw.is_valid():
                            weights.remove(pw)
                        return piece
                    break

        # Create end filler piece
        return self._create_end_filler(x, y, z, direction, depth)

    def _update_piece_weight(self, weights: List[PieceWeight]) -> int:
        """Update and calculate total weight"""
        has_valid = False
        total = 0

        for pw in weights:
            if pw.max_place_count > 0 and pw.place_count < pw.max_place_count:
                has_valid = True
            total += pw.weight

        return total if has_valid else -1

    def _create_piece(self, piece_type: PieceType, x: int, y: int, z: int,
                      direction: Direction, depth: int) -> Optional[StructurePiece]:
        """Create piece of specified type"""
        dims = self.PIECE_DIMENSIONS.get(piece_type)
        offsets = self.PIECE_OFFSETS.get(piece_type)

        if not dims or not offsets:
            return None

        box = BoundingBox.orient_box(x, y, z, offsets[0], offsets[1], offsets[2],
                                      dims[0], dims[1], dims[2], direction)

        if not self._is_ok_box(box):
            return None

        if self._find_collision(box):
            return None

        return StructurePiece(piece_type, box, direction, depth)

    def _create_end_filler(self, x: int, y: int, z: int, direction: Direction,
                           depth: int) -> Optional[StructurePiece]:
        """Create end filler piece"""
        box = BoundingBox.orient_box(x, y, z, -1, -3, 0, 5, 10, 8, direction)

        if not self._is_ok_box(box):
            return None

        if self._find_collision(box):
            return None

        return StructurePiece(PieceType.BRIDGE_END_FILLER, box, direction, depth)

    def _is_ok_box(self, box: BoundingBox) -> bool:
        """Check if bounding box is valid"""
        return box.min_y > self.LOWEST_Y_POSITION

    def _find_collision(self, box: BoundingBox) -> bool:
        """Check if collides with existing pieces"""
        for piece in self.pieces:
            if piece.bounding_box.intersects(box):
                return True
        return False

    def get_bridge_crossings(self) -> List[StructurePiece]:
        """Get all bridge crossing pieces"""
        return [p for p in self.pieces
                if p.piece_type in [PieceType.BRIDGE_CROSSING, PieceType.START_PIECE]]