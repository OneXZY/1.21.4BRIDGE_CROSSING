"""
Nether Fortress Location Calculator Module
Based on Minecraft 1.21.4 RandomSpreadStructurePlacement algorithm
"""

import math
from random_source import WorldgenRandom


class StructureType:
    """Structure type constants"""
    FORTRESS = "fortress"
    BASTION = "bastion"


class FortressLocator:
    """Nether Fortress Location Finder"""

    # Fortress placement parameters (from StructureSets.java)
    SPACING = 27  # spacing
    SEPARATION = 4  # separation
    SALT = 30084232  # salt

    # Structure weights (from StructureSets.java NETHER_COMPLEXES)
    # Fortress weight = 2, Bastion weight = 3, total = 5
    FORTRESS_WEIGHT = 2
    BASTION_WEIGHT = 3
    TOTAL_WEIGHT = FORTRESS_WEIGHT + BASTION_WEIGHT  # 5

    def __init__(self, world_seed: int):
        self.world_seed = world_seed
        self.random = WorldgenRandom(0)

    def _is_fortress_at_chunk(self, chunk_x: int, chunk_z: int) -> bool:
        """
        Determine if the structure at this chunk is a Fortress or Bastion.

        Based on ChunkGenerator.java logic:
        - Uses setLargeFeatureSeed(levelSeed, chunkX, chunkZ)
        - Selects structure based on weight: Fortress=2, Bastion=3

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate

        Returns:
            True if Fortress, False if Bastion
        """
        # Use a separate random instance to not interfere with position calculation
        selection_random = WorldgenRandom(0)
        selection_random.set_large_feature_seed(self.world_seed, chunk_x, chunk_z)

        # Select structure based on weight
        # If random < FORTRESS_WEIGHT (2), it's a Fortress
        # Otherwise it's a Bastion
        selected = selection_random.next_int(self.TOTAL_WEIGHT)
        return selected < self.FORTRESS_WEIGHT

    def get_potential_fortress_chunk(self, chunk_x: int, chunk_z: int) -> tuple:
        """
        Get potential fortress chunk position for the given region

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate

        Returns:
            (chunk_x, chunk_z) Potential fortress chunk coordinates
        """
        # Calculate region coordinates
        region_x = math.floor(chunk_x / self.SPACING)
        region_z = math.floor(chunk_z / self.SPACING)

        # Set random seed
        self.random.set_large_feature_with_salt(self.world_seed, region_x, region_z, self.SALT)

        # Calculate offset range
        offset_range = self.SPACING - self.SEPARATION  # 27 - 4 = 23

        # LINEAR spread type: use nextInt directly
        offset_x = self.random.next_int(offset_range)
        offset_z = self.random.next_int(offset_range)

        # Calculate final chunk position
        fortress_chunk_x = region_x * self.SPACING + offset_x
        fortress_chunk_z = region_z * self.SPACING + offset_z

        return (fortress_chunk_x, fortress_chunk_z)

    def is_fortress_chunk(self, chunk_x: int, chunk_z: int) -> bool:
        """
        Check if the given chunk is a fortress generation chunk

        Args:
            chunk_x: Chunk X coordinate
            chunk_z: Chunk Z coordinate

        Returns:
            True if the chunk can generate a fortress
        """
        potential_chunk = self.get_potential_fortress_chunk(chunk_x, chunk_z)
        return potential_chunk[0] == chunk_x and potential_chunk[1] == chunk_z

    def find_fortresses_in_range(self, center_chunk_x: int, center_chunk_z: int,
                                  radius_chunks: int) -> list:
        """
        Find all REAL fortress positions within the specified range.
        Filters out Bastion Remnants (which share the same placement system).

        Args:
            center_chunk_x: Center chunk X coordinate
            center_chunk_z: Center chunk Z coordinate
            radius_chunks: Search radius (in chunks)

        Returns:
            List of fortress chunk coordinates [(chunk_x, chunk_z), ...]
        """
        fortresses = []

        # Calculate region range to check
        min_region_x = math.floor((center_chunk_x - radius_chunks) / self.SPACING)
        max_region_x = math.floor((center_chunk_x + radius_chunks) / self.SPACING)
        min_region_z = math.floor((center_chunk_z - radius_chunks) / self.SPACING)
        max_region_z = math.floor((center_chunk_z + radius_chunks) / self.SPACING)

        for region_x in range(min_region_x, max_region_x + 1):
            for region_z in range(min_region_z, max_region_z + 1):
                # Get structure position for this region
                self.random.set_large_feature_with_salt(self.world_seed, region_x, region_z, self.SALT)
                offset_range = self.SPACING - self.SEPARATION
                offset_x = self.random.next_int(offset_range)
                offset_z = self.random.next_int(offset_range)

                structure_chunk_x = region_x * self.SPACING + offset_x
                structure_chunk_z = region_z * self.SPACING + offset_z

                # Check if within search range
                if (abs(structure_chunk_x - center_chunk_x) <= radius_chunks and
                    abs(structure_chunk_z - center_chunk_z) <= radius_chunks):
                    # IMPORTANT: Check if this is a Fortress or Bastion
                    if self._is_fortress_at_chunk(structure_chunk_x, structure_chunk_z):
                        fortresses.append((structure_chunk_x, structure_chunk_z))

        return fortresses

    def chunk_to_block(self, chunk_x: int, chunk_z: int) -> tuple:
        """Convert chunk coordinates to block coordinates (chunk corner)"""
        return (chunk_x * 16, chunk_z * 16)

    def block_to_chunk(self, block_x: int, block_z: int) -> tuple:
        """Convert block coordinates to chunk coordinates"""
        return (block_x >> 4, block_z >> 4)