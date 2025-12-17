"""
Minecraft 1.21.4 Nether Fortress Quad (2x2) Crossing Finder
The authors are Claude and Onemeng123
Main Entry Program

Usage:
    python main.py <seed> [options]

Examples:
    python main.py 12345
    python main.py 12345 --range 1000
    python main.py 12345 --center 100 200
"""

import argparse
import sys
from typing import List, Tuple

from random_source import WorldgenRandom
from fortress_locator import FortressLocator
from fortress_generator import FortressGenerator, StructurePiece, PieceType
from crossing_detector import CrossingDetector, QuadCrossing, analyze_fortress_crossings


def find_quad_crossings_for_seed(world_seed: int, search_range: int = 5000,
                                 center_x: int = 0, center_z: int = 0,
                                 verbose: bool = False) -> List[dict]:
    """
    Find all quad crossings for specified seed

    Args:
        world_seed: World seed
        search_range: Search range (block coordinates)
        center_x: Search center X coordinate (blocks)
        center_z: Search center Z coordinate (blocks)
        verbose: Whether to output detailed info

    Returns:
        List of found quad crossing info
    """
    results = []

    # Convert to chunk coordinates
    center_chunk_x = center_x >> 4
    center_chunk_z = center_z >> 4
    range_chunks = search_range >> 4

    if verbose:
        print(f"Searching fortresses for seed {world_seed}...")
        print(f"Search range: center({center_x}, {center_z}), radius {search_range} blocks")

    # Find all fortresses in range
    locator = FortressLocator(world_seed)
    fortresses = locator.find_fortresses_in_range(center_chunk_x, center_chunk_z, range_chunks)

    if verbose:
        print(f"Found {len(fortresses)} fortress locations")

    # Analyze each fortress
    for i, (chunk_x, chunk_z) in enumerate(fortresses):
        if verbose:
            print(f"\nAnalyzing fortress {i+1}/{len(fortresses)}: chunk({chunk_x}, {chunk_z})")

        # Generate fortress structure
        generator = FortressGenerator(world_seed, chunk_x, chunk_z)
        pieces = generator.generate()

        # Get crossings
        crossings = generator.get_bridge_crossings()

        if verbose:
            print(f"  Generated {len(pieces)} structure pieces")
            print(f"  Including {len(crossings)} crossings")

        # Analyze crossings
        analysis = analyze_fortress_crossings(crossings)

        if analysis['has_quad']:
            for quad in analysis['quad_crossings']:
                block_x = chunk_x * 16
                block_z = chunk_z * 16

                result = {
                    'fortress_chunk': (chunk_x, chunk_z),
                    'fortress_block': (block_x, block_z),
                    'quad_crossing': quad,
                    'total_crossings': analysis['total_crossings']
                }
                results.append(result)

                if verbose:
                    print(f"  *** Found quad crossing! ***")
                    print(f"      {quad}")

    return results


def print_results(results: List[dict], world_seed: int):
    """Print search results"""
    print("\n" + "=" * 60)
    print(f"Search Results - Seed: {world_seed}")
    print("=" * 60)

    if not results:
        print("\nNo quad (2x2) crossings found")
        print("\nTips: Quad crossings are very rare, you can try:")
        print("  1. Expand search range (--range parameter)")
        print("  2. Try other seeds")
        return

    print(f"\nFound {len(results)} quad crossing(s)!")

    for i, result in enumerate(results):
        print(f"\n--- Quad Crossing #{i+1} ---")
        print(f"Fortress chunk: ({result['fortress_chunk'][0]}, {result['fortress_chunk'][1]})")
        print(f"Fortress block: ({result['fortress_block'][0]}, {result['fortress_block'][1]})")
        print(f"Total crossings in fortress: {result['total_crossings']}")

        quad = result['quad_crossing']
        print(f"\nQuad crossing details:")
        print(f"  Center: X={quad.center[0]}, Y={quad.center[1]}, Z={quad.center[2]}")
        print(f"  Range: ({quad.bounding_box.min_x}, {quad.bounding_box.min_z}) -> "
              f"({quad.bounding_box.max_x}, {quad.bounding_box.max_z})")

        print(f"\n  Individual crossing positions:")
        for j, crossing in enumerate(quad.crossings):
            center = crossing.get_center()
            print(f"    {j+1}. X={center[0]}, Y={center[1]}, Z={center[2]} "
                  f"(type: {crossing.piece_type.value})")

    print("\n" + "=" * 60)
    print("Nether coordinate tip: Y=64 is the standard fortress height in the Nether")
    print("=" * 60)


def analyze_single_fortress(world_seed: int, chunk_x: int, chunk_z: int):
    """Analyze single fortress details"""
    print(f"\nAnalyzing fortress: seed={world_seed}, chunk=({chunk_x}, {chunk_z})")
    print("-" * 50)

    generator = FortressGenerator(world_seed, chunk_x, chunk_z)
    pieces = generator.generate()

    # Count piece types
    type_counts = {}
    for piece in pieces:
        type_name = piece.piece_type.value
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    print(f"\nStructure piece statistics (total {len(pieces)}):")
    for type_name, count in sorted(type_counts.items()):
        print(f"  {type_name}: {count}")

    # Get crossings
    crossings = generator.get_bridge_crossings()
    print(f"\nCrossing count: {len(crossings)}")

    if crossings:
        print("\nCrossing positions:")
        for i, crossing in enumerate(crossings):
            center = crossing.get_center()
            print(f"  {i+1}. X={center[0]}, Y={center[1]}, Z={center[2]}")

    # Analyze quad crossings
    analysis = analyze_fortress_crossings(crossings)

    if analysis['has_quad']:
        print(f"\n*** Found {len(analysis['quad_crossings'])} quad crossing(s)! ***")
        for quad in analysis['quad_crossings']:
            print(f"  {quad}")
    else:
        print("\nNo quad crossings found")

    # Show connected groups
    if analysis['connected_groups']:
        print(f"\nConnected crossing groups: {len(analysis['connected_groups'])} group(s)")
        for i, group in enumerate(analysis['connected_groups']):
            print(f"  Group {i+1}: {len(group)} crossings")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Minecraft 1.21.4 Nether Fortress Quad (2x2) Crossing Finder',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py 12345                    # Search seed 12345
  python main.py 12345 --range 2000       # Expand search range to 2000 blocks
  python main.py 12345 --center 1000 500  # Search from coordinates (1000, 500)
  python main.py 12345 --analyze 10 20    # Analyze fortress at chunk (10, 20)

Notes:
  - Quad crossings are very rare, may need to search multiple seeds
  - Larger search range takes longer
  - Coordinates are Nether coordinates (block coordinates)
        """
    )

    parser.add_argument('seed', type=int, help='Minecraft world seed')
    parser.add_argument('--range', '-r', type=int, default=5000,
                        help='Search radius (block coordinates, default 5000)')
    parser.add_argument('--center', '-c', type=int, nargs=2, default=[0, 0],
                        metavar=('X', 'Z'), help='Search center coordinates (default 0 0)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')
    parser.add_argument('--analyze', '-a', type=int, nargs=2,
                        metavar=('CHUNK_X', 'CHUNK_Z'),
                        help='Analyze fortress at specified chunk')

    args = parser.parse_args()

    print("=" * 60)
    print("Minecraft 1.21.4 Nether Fortress Quad Crossing Finder")
    print("=" * 60)

    if args.analyze:
        # Analyze single fortress
        analyze_single_fortress(args.seed, args.analyze[0], args.analyze[1])
    else:
        # Search for quad crossings
        results = find_quad_crossings_for_seed(
            args.seed,
            search_range=args.range,
            center_x=args.center[0],
            center_z=args.center[1],
            verbose=args.verbose
        )
        print_results(results, args.seed)


if __name__ == '__main__':
    main()