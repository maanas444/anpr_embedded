"""led_matrix.py - Sense HAT checkmark, cross, and scrolling text."""

from sense_hat import SenseHat

GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

CHECKMARK = [
    0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,1,0,
    0,0,0,0,0,1,0,0,
    0,0,0,0,1,0,0,0,
    1,0,0,1,0,0,0,0,
    0,1,1,0,0,0,0,0,
    0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,
]

CROSS = [
    0,0,0,0,0,0,0,0,
    0,1,0,0,0,1,0,0,
    0,0,1,0,1,0,0,0,
    0,0,0,1,0,0,0,0,
    0,0,0,1,0,0,0,0,
    0,0,1,0,1,0,0,0,
    0,1,0,0,0,1,0,0,
    0,0,0,0,0,0,0,0,
]

hat = SenseHat()


def show_checkmark():
    hat.set_pixels([GREEN if p else BLACK for p in CHECKMARK])


def show_cross():
    hat.set_pixels([RED if p else BLACK for p in CROSS])


def scroll_text(text):
    hat.show_message(text)


if __name__ == "__main__":
    show_checkmark()
    import time; time.sleep(2)
    show_cross()
    time.sleep(2)
    scroll_text("ABC123")
    hat.clear()