"""
led_matrix.py

Wraps the Sense HAT 8x8 LED matrix to provide the visual status feedback
required by the ALPR system:
    - Green checkmark  -> plate recognised / logged successfully
    - Red cross        -> plate not recognised / rejected
    - Scrolling text   -> plate string / status message

Run directly on the Raspberry Pi (real Sense HAT required):
    python3 led_matrix.py
"""

from sense_hat import SenseHat

# Colours (R, G, B)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# 8x8 pixel maps. 1 = coloured pixel, 0 = off.
_CHECKMARK_MAP = [
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 1, 0,
    0, 0, 0, 0, 0, 1, 0, 0,
    0, 0, 0, 0, 1, 0, 0, 0,
    1, 0, 0, 1, 0, 0, 0, 0,
    0, 1, 1, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
]

_CROSS_MAP = [
    0, 0, 0, 0, 0, 0, 0, 0,
    0, 1, 0, 0, 0, 1, 0, 0,
    0, 0, 1, 0, 1, 0, 0, 0,
    0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 0, 1, 0, 0, 0, 0,
    0, 0, 1, 0, 1, 0, 0, 0,
    0, 1, 0, 0, 0, 1, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0,
]


class LedMatrix:
    """Encapsulates all Sense HAT LED matrix operations."""

    def __init__(self, rotation: int = 0, low_light: bool = True):
        """
        rotation: rotate the display (0, 90, 180, 270) to match physical
                  mounting orientation of the Sense HAT on the enclosure.
        low_light: dims the matrix, useful since the ALPR unit may run
                   in low-light car park conditions and a full-brightness
                   matrix can be dazzling / draw more current.
        """
        self.hat = SenseHat()
        self.hat.set_rotation(rotation)
        self.hat.low_light = low_light
        self.clear()

    def clear(self):
        """Turn off all pixels."""
        self.hat.clear()

    def show_checkmark(self, colour=GREEN, background=BLACK):
        """Draw a checkmark graphic - plate accepted / logged."""
        pixels = [colour if p else background for p in _CHECKMARK_MAP]
        self.hat.set_pixels(pixels)

    def show_cross(self, colour=RED, background=BLACK):
        """Draw a cross graphic - plate rejected / not recognised."""
        pixels = [colour if p else background for p in _CROSS_MAP]
        self.hat.set_pixels(pixels)

    def scroll_text(self, text: str, speed: float = 0.05, colour=WHITE,
                     background=BLACK, loop: bool = False):
        """
        Slide text across the LED matrix.

        text:       string to display (e.g. a sanitised plate string,
                    or a status message).
        speed:      scroll speed. Lower = faster. Passed straight to
                    the Sense HAT's scroll_message 'scroll_speed'.
        colour:     text colour RGB tuple.
        background: background colour RGB tuple.
        loop:       if True, keep scrolling the message repeatedly.
                    show_message() call blocks until finished scrolling
                    once; set loop=True to call this in its own thread
                    if you need it to repeat without blocking the caller.
        """
        self.hat.show_message(
            text,
            scroll_speed=speed,
            text_colour=colour,
            back_colour=background,
        )
        if loop:
            self.scroll_text(text, speed, colour, background, loop=True)


if __name__ == "__main__":
    # Simple manual test - run this directly on the Pi to sanity check
    # the display.
    import time

    matrix = LedMatrix()

    print("Showing green checkmark...")
    matrix.show_checkmark()
    time.sleep(2)

    print("Showing red cross...")
    matrix.show_cross()
    time.sleep(2)

    print("Scrolling text...")
    matrix.scroll_text("ABC123")

    matrix.clear()
    print("Done.")