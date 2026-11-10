"""Offline demo: process stdin packets and write simulated responses to stdout."""
import argparse
import sys

from .engine import BubbaEngine
from .session import OfflineSession


def main(argv=None):
    parser = argparse.ArgumentParser(description="BubbaBot offline MRC packet simulator")
    parser.add_argument("--room", action="append", required=True,
                        help="Allowed room (repeat for multiple rooms)")
    args = parser.parse_args(argv)
    session = OfflineSession(BubbaEngine(allowed_rooms=args.room))
    print("Offline simulation only; no MRC network connection.", file=sys.stderr)
    session.run(sys.stdin, sys.stdout)


if __name__ == "__main__":
    main()
