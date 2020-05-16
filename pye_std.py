#
# Wrapper for Micropython standard console IO
#
import sys

## test, if the Editor class is already in this file
try:
    type(Editor)
except NameError:
    ## no, import it.
    from pye_core import pye_edit, is_micropython

class IO_DEVICE:
    def __init__(self):
        try:
            from micropython import kbd_intr
            kbd_intr(-1)
        except ImportError:
            pass
        if hasattr(sys.stdin, "buffer"):
            self.rd_raw_fct = sys.stdin.buffer.read
        else:
            self.rd_raw_fct = sys.stdin.read

    def wr(self, s):
        sys.stdout.write(s)

    def rd(self):
        return sys.stdin.read(1)

    def rd_raw(self):
        return self.rd_raw_fct(1)

    def deinit_tty():
        try:
            from micropython import kbd_intr
            kbd_intr(3)
        except ImportError:
            pass

    def get_screen_size(self):
        self.wr('\x1b[999;999H\x1b[6n')
        pos = ''
        char = self.rd() ## expect ESC[yyy;xxxR
        while char != 'R':
            pos += char
            char = self.rd()
        return [int(i, 10) for i in pos.lstrip("\n\x1b[").split(';')]

def pye(*args, tab_size=4, undo=50):
    pye_edit(*args, tab_size=tab_size, undo=undo, io_device=IO_DEVICE(0))