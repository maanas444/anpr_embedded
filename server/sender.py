#!/usr/bin/env python3
"""
sender.py
---------
Sends data to the PHP web server as an HTTP GET request, using URL
parameters. This simulates an embedded module (e.g. a camera doing
license plate recognition) reporting a reading to the server.
Usage:
 python3 sender.py <license_plate> <camera_id>
Example:
 python3 sender.py EAG942 12
"""

import sys
import urllib.request
import urllib.parse

# Change this to your Pi's IP address if the sender runs on a
# different machine than the webserver, e.g.:
# SERVER_URL = "http://192.168.1.142/receiver.php"
SERVER_URL = "http://localhost/receiver.php"


def send_data(license_plate: str, camera_id: str) -> None:
    """Send license_plate and camera as URL parameters to the PHP server."""
    # urlencode automatically escapes spaces and special characters
    # (e.g. a space becomes %20), so the data is safe to put in a URL.
    params = urllib.parse.urlencode(
        {
            "license_plate": license_plate,
            "camera": camera_id,
        }
    )
    url = f"{SERVER_URL}?{params}"

    print(f"Sending request to: {url}")
    try:

        with urllib.request.urlopen(url) as response:
            body = response.read().decode()
            print("Server response:")
            print(body)
    except urllib.error.URLError as e:
        print(f"Error: could not reach server ({e})")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        plate = sys.argv[1]
        camera = sys.argv[2]
    else:
        plate = "EAG942"
        camera = "12"
        print(
            f"No arguments given, using example values: "
            f"license_plate={plate}, camera={camera}"
        )
    send_data(plate, camera)
