#!/usr/bin/env python3
"""
receiver.py
-----------
Called by receiver.php with the data as command line arguments.
Prints the received data to the console (which, when called via
Apache, ends up in receiver.php's output / shell_exec capture).
Usage (normally called automatically by receiver.php):
 python3 receiver.py <license_plate> <camera_id>
Example output:
 License Plate: EAG942; Camera: 12
"""

import sys


def main() -> None:
    if len(sys.argv) < 3:
        print("Error: expected 2 arguments (license_plate, camera)")
        sys.exit(1)
    license_plate = sys.argv[1]
    camera = sys.argv[2]

    print(f"License Plate: {license_plate}; Camera: {camera}")


if __name__ == "__main__":
    main()
