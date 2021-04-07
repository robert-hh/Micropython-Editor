#
# Front-end for Linux
#
import os, tty, signal, termios, sys

class SignalWindowResize(Exception):
    pass

class IO_DEVICE:
    def __init__(self, device, key_redraw):
        self.org_termios = termios.tcgetattr(device)
        tty.setraw(device)
        self.sdev = device
        self.key_redraw = key_redraw

    def wr(self, s):
        os.write(1, s.encode("utf-8"))

    def rd(self):
        while True:
            try: ## The signal handler for SIGWINCH raises an exception
                c = os.read(self.sdev, 1)
                flag = c[0]
                while (flag & 0xc0) == 0xc0:  ## utf-8 char collection
                    c += os.read(self.sdev, 1)
                    flag <<= 1
                return c.decode("utf-8")
            except SignalWindowResize:
                return chr(self.key_redraw)

    def rd_raw(self):
        return os.read(self.sdev,1)

    def get_screen_size(self):
        if hasattr(signal, "SIGWINCH"):
            signal.signal(signal.SIGWINCH, signal.SIG_IGN)
        self.wr('\x1b[999;999H\x1b[6n')
        pos = ''
        char = self.rd() ## expect ESC[yyy;xxxR
        while char != 'R':
            pos += char
            char = self.rd()
        if hasattr(signal, "SIGWINCH"):
            signal.signal(signal.SIGWINCH, IO_DEVICE.signal_handler)
        return [int(i, 10) for i in pos.lstrip("\n\x1b[").split(';')]

    def deinit_tty(self):
        termios.tcsetattr(self.sdev, termios.TCSANOW, self.org_termios)

    @staticmethod
    def signal_handler(sig, frame):
        raise SignalWindowResize  ## raise the specific exception, which stops os.read()

## test, if the Editor class is already present
if "pye_edit" not in globals().keys():
    from pye import pye_edit, is_micropython, KEY_REDRAW, Editor

Editor.match_span = 500

def pye(*args, tab_size=4, undo=500):
    io_device = IO_DEVICE(0, KEY_REDRAW)
    ret = pye_edit(*args, tab_size=tab_size, undo=undo, io_device=io_device)
    io_device.deinit_tty()
    return ret

if __name__ == "__main__":
    import stat
    fd_tty = 0
    if len(sys.argv) > 1:
        name = sys.argv[1:]
        io_device = IO_DEVICE(fd_tty, KEY_REDRAW)
        pye_edit(name, undo=500, io_device=io_device)
    else:
        name = "."
        if not is_micropython:
            mode = os.fstat(0).st_mode
            if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
                name = [[l.rstrip('\r\n\t ').expandtabs(8) for l in sys.stdin]]
                os.close(0) ## close and repopen /dev/tty
        fd_tty = os.open("/dev/tty", os.O_RDONLY) ## memorized, if new fd
        io_device = IO_DEVICE(fd_tty, KEY_REDRAW)
        pye_edit(name, undo=500, io_device=io_device)

    io_device.deinit_tty()
