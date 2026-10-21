"""Temporary entry point to manually test the parser."""
import sys

from model import ParseError
from parsing import Parser  # adjust to your package name (see below)


def main() -> int:
    """Parse the map given as argument and print what was read."""
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <map_file>", file=sys.stderr)
        return 1
    try:
        nb_drones, zones, connections = Parser(sys.argv[1]).parse()
    except ParseError as error:
        print(error, file=sys.stderr)
        return 1

    print(f"nb_drones: {nb_drones}")
    print(f"\nZones ({len(zones)}):")
    for zone in zones:
        print(f"  {zone}")
    print(f"\nConnections ({len(connections)}):")
    for connection in connections:
        print(f"  {connection}")
    return 0


if __name__ == "__main__":
    sys.exit(main())