#
# Front-end for Micropython standard console IO
#
try:
    import usys as sys
except:
    import sys

class IO_DEVICE:

    def __init__(self):
        self.rd_raw_fct = self.rd
        self.peek_char = None

    def wr(self, s):
        from msvcrt import putwch
        for c in s:
            putwch(c)

    def rd(self):
        from msvcrt import getwch
        if self.peek_char is not None:
            c = self.peek_char
            self.peek_char = None
            return c
        c = getwch()
        if ord(c) == 224 or c == '\x00': # translate the keyboard escape sequences
            c = getwch()
            try:  # borrowed from mpr.py
                self.peek_char = {"H": "A",  # UP
                                "P": "B",  # DOWN
                                "M": "C",  # RIGHT
                                "K": "D",  # LEFT
                                "G": "H",  # POS1
                                "O": "F",  # END
                                "Q": "6~",  # PGDN
                                "I": "5~",  # PGUP
                                "s": "1;5D",  # CTRL-LEFT,
                                "t":"1;5C",  # CTRL-RIGHT,
                                "\x8d": "1;5A",  #  CTRL-UP,
                                "\x91": "1;5B",  # CTRL-DOWN,
                                "w" : "1;5H",  # CTRL-POS1
                                "u" : "1;5F", # CTRL-END
                                "\x98": "1;3A",  #  ALT-UP,
                                "\xa0": "1;3B",  # ALT-DOWN,
                                "S" : "3~",  # DEL,
                                "\x93": "3;5~",  # CTRL-DEL
                                "\x94" :"Z",  # Ctrl-Tab = BACKTAB,
                                }[c]
            except:
                self.peek_char = "~"  # illegal code, will be ignored
            return "\x1b["
        else:
            return c

    def rd_raw(self):
        return self.rd_raw_fct(1)

    def deinit_tty(self):
        pass

    def get_screen_size(self):
        self.wr('\x1b[999;999H\x1b[6n')
        pos = ''
        char = self.rd() ## expect ESC[yyy;xxxR
        while char != 'R':
            pos += char
            char = self.rd()
        return [int(i, 10) for i in pos.lstrip(" \n\x1b[").split(';')]

## test, if the Editor class is already present
if "pye_edit" not in globals().keys():
    from pye import pye_edit, Editor, KEY_BACKSPACE

Editor.KEYMAP["\x08"] = KEY_BACKSPACE
Editor.match_span = 500

def pye(*args, tab_size=4, undo=500):
    io_device = IO_DEVICE()
    ret = pye_edit(*args, tab_size=tab_size, undo=undo, io_device=io_device)
    io_device.deinit_tty()
    return ret

if __name__ == "__main__":
    io_device = IO_DEVICE()
    if len(sys.argv) > 1:
        name = sys.argv[1:]
        pye_edit(name, undo=500, io_device=io_device)
    else:
        name = "."
        pye_edit(name, undo=500, io_device=io_device)

    io_device.deinit_tty()
