##
## Small python text editor based on the
## Very simple VT100 terminal text editor widget
## Copyright (c) 2015 Paul Sokolovsky (initial code)
## Copyright (c) 2015 Robert Hammelrath (additional code)
## Distributed under MIT License
## Changes:
## - Ported the code to pyboard (still runs on Linux Python3 and on Linux Micropython)
##   It uses VCP_USB on Pyboard, but that may easyly be changed to UART
## - changed read keyboard function to comply with char-by-char input (on serial lines)
## - added support for TAB, BACKTAB, SAVE, DEL at end joining lines, Find,
## - Goto Line, Yank (delete line into buffer), Zap (insert buffer), UNDO, GET file
## - moved main into a function with some optional parameters
## - Added a status line, line number column and single line prompts for Quit, Save, Find and Goto
## - Added mouse support for pointing and scrolling
##
import sys, gc
#ifdef LINUX
if sys.platform in ("linux", "darwin"):
    import os, signal, tty, termios
#endif
#ifdef DEFINES
#define KEY_UP          0x0b
#define KEY_DOWN        0x0d
#define KEY_LEFT        0x0c
#define KEY_RIGHT       0x0f
#define KEY_HOME        0x10
#define KEY_END         0x11
#define KEY_PGUP        0x17
#define KEY_PGDN        0x19
#define KEY_QUIT        0x03
#define KEY_ENTER       0x0a
#define KEY_BACKSPACE   0x08
#define KEY_DELETE      0x1f
#define KEY_WRITE       0x13
#define KEY_TAB         0x09
#define KEY_BACKTAB     0x15
#define KEY_FIND        0x06
#define KEY_GOTO        0x07
#define KEY_FIRST       0x02
#define KEY_LAST        0x14
#define KEY_FIND_AGAIN  0x0e
#define KEY_YANK        0x18
#define KEY_ZAP         0x16
#define KEY_TOGGLE      0x01
#define KEY_REPLC       0x12
#define KEY_DUP         0x04
#define KEY_MOUSE       0x1b
#define KEY_SCRLUP      0x1c
#define KEY_SCRLDN      0x1d
#define KEY_REDRAW      0x05
#define KEY_UNDO        0x1a
#define KEY_GET         0x1e
#else
KEY_UP        = 0x0b
KEY_DOWN      = 0x0d
KEY_LEFT      = 0x0c
KEY_RIGHT     = 0x0f
KEY_HOME      = 0x10
KEY_END       = 0x11
KEY_PGUP      = 0x17
KEY_PGDN      = 0x19
KEY_QUIT      = 0x03
KEY_ENTER     = 0x0a
KEY_BACKSPACE = 0x08
KEY_DELETE    = 0x1f
KEY_WRITE     = 0x13
KEY_TAB       = 0x09
KEY_BACKTAB   = 0x15
KEY_FIND      = 0x06
KEY_GOTO      = 0x07
KEY_MOUSE     = 0x1b
KEY_SCRLUP    = 0x1c
KEY_SCRLDN    = 0x1d
KEY_FIND_AGAIN= 0x0e
KEY_REDRAW    = 0x05
KEY_UNDO      = 0x1a
KEY_YANK      = 0x18
KEY_ZAP       = 0x16
KEY_DUP       = 0x04
KEY_FIRST     = 0x02
KEY_LAST      = 0x14
KEY_REPLC     = 0x12
KEY_MOUSE     = 0x1b
KEY_SCRLUP    = 0x1c
KEY_SCRLDN    = 0x1d
KEY_TOGGLE    = 0x01
KEY_GET       = 0x1e
#endif

class Editor:

    KEYMAP = { ## Gets lengthy
    b"\x1b[A" : KEY_UP,
    b"\x1b[B" : KEY_DOWN,
    b"\x1b[D" : KEY_LEFT,
    b"\x1b[C" : KEY_RIGHT,
    b"\x1b[H" : KEY_HOME, ## in Linux Terminal
    b"\x1bOH" : KEY_HOME, ## Picocom, Minicom
    b"\x1b[1~": KEY_HOME, ## Putty
    b"\x1b[F" : KEY_END,  ## Linux Terminal
    b"\x1bOF" : KEY_END,  ## Picocom, Minicom
    b"\x1b[4~": KEY_END,  ## Putty
    b"\x1b[5~": KEY_PGUP,
    b"\x1b[6~": KEY_PGDN,
    b"\x11"   : KEY_QUIT, ## Ctrl-Q
    b"\x03"   : KEY_QUIT, ## Ctrl-C
    b"\r"     : KEY_ENTER,
    b"\n"     : KEY_ENTER,
    b"\x7f"   : KEY_BACKSPACE, ## Ctrl-? (127)
    b"\x08"   : KEY_BACKSPACE,
    b"\x1b[3~": KEY_DELETE,
    b"\x13"   : KEY_WRITE,  ## Ctrl-S
    b"\x06"   : KEY_FIND, ## Ctrl-F
    b"\x0e"   : KEY_FIND_AGAIN, ## Ctrl-N
    b"\x07"   : KEY_GOTO, ##  Ctrl-G
    b"\x05"   : KEY_REDRAW, ## Ctrl-E
    b"\x1a"   : KEY_UNDO, ## Ctrl-Z
    b"\x09"   : KEY_TAB,
    b"\x15"   : KEY_BACKTAB, ## Ctrl-U
    b"\x1b[Z" : KEY_BACKTAB, ## Shift Tab
    b"\x18"   : KEY_YANK, ## Ctrl-X
    b"\x1b[3;5~": KEY_YANK, ## Ctrl-Del
    b"\x16"   : KEY_ZAP, ## Ctrl-V
    b"\x04"   : KEY_DUP, ## Ctrl-D
    b"\x12"   : KEY_REPLC, ## Ctrl-R
    b"\x1b[M" : KEY_MOUSE,
    b"\x01"   : KEY_TOGGLE, ## Ctrl-A
    b"\x14"   : KEY_FIRST, ## Ctrl-T
    b"\x02"   : KEY_LAST,  ## Ctrl-B
    b"\x1b[1;5H": KEY_FIRST,
    b"\x1b[1;5F": KEY_LAST,
    b"\x0f"   : KEY_GET, ## Ctrl-O
    }

    def __init__(self, tab_size, undo_limit):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.margin = 0
        self.tab_size = tab_size
        self.changed = ' '
        self.sticky_c = " "
        self.message = " "
        self.find_pattern = ""
        self.fname = None
        self.content = [""]
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
        self.yank_buffer = []
        self.lastkey = 0
        self.case = "n"
        self.autoindent = "y"
#ifndef BASIC
        self.replc_pattern = ""
        self.write_tabs = "n"
#endif
#ifdef LINUX
    if sys.platform in ("linux", "darwin"):
        @staticmethod
        def wr(s):
            if isinstance(s, str):
                s = bytes(s, "utf-8")
            os.write(1, s)

        @staticmethod
        def rd():
            while True:
                try: ## WINCH causes interrupt
                    return os.read(Editor.sdev,1)
                except:
                    if Editor.winch: ## simulate REDRAW key
                        Editor.winch = False
                        return b'\x05'

        def init_tty(self, device, baud):
            self.org_termios = termios.tcgetattr(device)
            tty.setraw(device)
            Editor.sdev = device
            if sys.implementation.name == "cpython":
                signal.signal(signal.SIGWINCH, Editor.signal_handler)

        def deinit_tty(self):
            import termios
            termios.tcsetattr(Editor.sdev, termios.TCSANOW, self.org_termios)

        @staticmethod
        def signal_handler(sig, frame):
            signal.signal(signal.SIGWINCH, signal.SIG_IGN)
            Editor.winch = True
            return True
#endif
#ifdef PYBOARD
    if sys.platform == "pyboard":
        @staticmethod
        def wr(s):
            ns = 0
            while ns < len(s): # complicated but needed, since USB_VCP.write() has issues
                res = Editor.serialcomm.write(s[ns:])
                if res != None:
                    ns += res

        @staticmethod
        def rd():
            while not Editor.serialcomm.any():
                pass
            return Editor.serialcomm.read(1)

        def init_tty(self, device, baud):
            import pyb
            Editor.sdev = device
            if Editor.sdev:
                Editor.serialcomm = pyb.UART(device, baud)
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)

        def deinit_tty(self):
            if not Editor.sdev:
                Editor.serialcomm.setinterrupt(3)
#endif
#ifdef WIPY
    if sys.platform == "WiPy":
        @staticmethod
        def wr(s):
            ns = 0
            while ns < len(s): # trial, since Telnet sometimes lags
                res = Editor.serialcomm.write(s[ns:])
                if res != None:
                    ns += res

        @staticmethod
        def rd():
            if Editor.sdev:
                while not Editor.serialcomm.any():
                    pass
                return Editor.serialcomm.read(1)
            else:
                while True:
                    try:
                        ch = sys.stdin.read(1)
                        if ch != "\x00":
                            return ch.encode()
                    except: pass

        def init_tty(self, device, baud):
            import machine
            if device:
                Editor.serialcomm = machine.UART(device - 1, baud)
            else:
                Editor.serialcomm = sys.stdout
            Editor.sdev = device

        def deinit_tty(self):
            pass
#endif
    @staticmethod
    def goto(row, col):
        Editor.wr("\x1b[%d;%dH" % (row + 1, col + 1))

    @staticmethod
    def clear_to_eol():
        Editor.wr(b"\x1b[0K")

    @staticmethod
    def cursor(onoff):
        if onoff:
            Editor.wr(b"\x1b[?25h")
        else:
            Editor.wr(b"\x1b[?25l")

    @staticmethod
    def hilite(mode):
        if mode == 1:
            Editor.wr(b"\x1b[1m")
        else:
            Editor.wr(b"\x1b[0m")

#ifndef BASIC
    @staticmethod
    def mouse_reporting(onoff):
        if onoff:
            Editor.wr('\x1b[?9h') ## enable mouse reporting
        else:
            Editor.wr('\x1b[?9l') ## disable mouse reporting
#endif
    @staticmethod
    def scroll_region(stop):
        if stop:
            Editor.wr('\x1b[1;%dr' % stop) ## enable partial scrolling
        else:
            Editor.wr('\x1b[r') ## full scrolling

    def scroll_up(self, scrolling):
        self.scrbuf[scrolling:] = self.scrbuf[:-scrolling]
        self.scrbuf[:scrolling] = [''] * scrolling
        self.goto(0, 0)
        Editor.wr("\x1bM" * scrolling)

    def scroll_down(self, scrolling):
        self.scrbuf[:-scrolling] = self.scrbuf[scrolling:]
        self.scrbuf[-scrolling:] = [''] * scrolling
        self.goto(self.height - 1, 0)
        Editor.wr("\x1bD " * scrolling)

    def set_screen_parms(self):
        self.cursor(False)
        Editor.wr('\x1b[999;999H\x1b[6n')
        pos = b''
        char = Editor.rd() ## expect ESC[yyy;xxxR
        while char != b'R':
            if char in b"0123456789;": pos += char
            char = Editor.rd()
        (self.height, self.width) = [int(i, 10) for i in pos.split(b';')]
        self.height -= 1
        self.scrbuf = ["\x01"] * self.height ## force delete
        self.scroll_region(self.height)

    def get_input(self):  ## read from interface/keyboard one byte each and match against function keys
        while True:
            input = Editor.rd()
            if input == b'\x1b': ## starting with ESC, must be fct
                while True:
                    input += Editor.rd()
                    c = chr(input[-1])
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
            if input in self.KEYMAP:
                c = self.KEYMAP[input]
                if c != KEY_MOUSE:
                    return c
#ifndef BASIC
                else: ## special for mice
                    mf = ord((Editor.rd())) & 0xe3 ## read 3 more chars
                    self.mouse_x = ord(Editor.rd()) - 33
                    self.mouse_y = ord(Editor.rd()) - 33
                    if mf == 0x61:
                        return KEY_SCRLDN
                    elif mf == 0x60:
                        return KEY_SCRLUP
                    else:
                        return KEY_MOUSE ## do nothing but set the cursor
#endif
            elif input[0] >= 0x20: ## but only if no Ctrl-Char
                return input[0]

    def display_window(self): ## Update window and status line
## Force cur_line and col to be in the reasonable bounds
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
        self.col = max(0, min(self.col, len(self.content[self.cur_line])))
## Check if Column is out of view, and align margin if needed
        if self.col >= self.width + self.margin:
            self.margin = self.col - self.width + (self.width >> 2)
        elif self.col < self.margin:
            self.margin = max(self.col - (self.width >> 2), 0)
## if cur_line is out of view, align top_line to the given row
        if not (self.top_line <= self.cur_line < self.top_line + self.height): # Visible?
            self.top_line = max(self.cur_line - self.row, 0)
## in any case, align row to top_line and cur_line
        self.row = self.cur_line - self.top_line
## update_screen
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: ## at empty bottom screen part
                if self.scrbuf[c] != '':
                    Editor.goto(c, 0)
                    self.clear_to_eol()
                    self.scrbuf[c] = ''
            else:
                l = self.content[i][self.margin:self.margin + self.width]
                if l != self.scrbuf[c]: ## line changed, print it
                    Editor.goto(c, 0)
                    self.wr(l)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = l
                i += 1
## display Status-Line
        self.goto(self.height, 0)
        self.hilite(1)
        self.clear_to_eol() ## moved up for mate/xfce4-terminal issue with scroll region
        self.wr("[%d] %c Row: %d Col: %d  %s" % (self.total_lines, self.changed, self.cur_line + 1, self.col + 1, self.message[:self.width - 25]))
        self.hilite(0)
        self.cursor(True)
        self.goto(self.row, self.col - self.margin)

    @staticmethod
    def spaces(line, pos = None): ## count spaces
        if pos == None: ## at line start
            return len(line) - len(line.lstrip(" "))
        else: ## left to the cursor
            return len(line[:pos]) - len(line[:pos].rstrip(" "))

    def line_edit(self, prompt, default):  ## simple one: only 4 fcts
        self.goto(self.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        while True:
            key = self.get_input()  ## Get Char of Fct.
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(0)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(0)
                return None
            elif key == KEY_BACKSPACE: ## Backspace
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == KEY_DELETE: ## Delete prev. Entry
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: ## char to be added at the end
                if len(prompt) + len(res) < self.width - 2:
                    res += chr(key)
                    self.wr(chr(key))

    def find_in_file(self, pattern, pos):
        self.find_pattern = pattern # remember it
        if self.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, self.total_lines):
            if self.case != "y":
                match = self.content[line][spos:].lower().find(pattern)
#ifndef BASIC
            else:
                match = self.content[line][spos:].find(pattern)
#endif
            if match >= 0:
                break
            spos = 0
        else:
            self.message = "No match: " + pattern
            return 0
        self.col = match + spos
        self.cur_line = line
        self.message = ' ' ## force status once
        return len(pattern)

    def cursor_down(self):
        if self.cur_line < self.total_lines - 1:
            self.cur_line += 1
            if self.cur_line == self.top_line + self.height:
                self.scroll_down(1)

    def handle_cursor_keys(self, key): ## keys which move, sanity checks later
        if key == KEY_DOWN:
            self.cursor_down()
        elif key == KEY_UP:
            if self.cur_line > 0:
                self.cur_line -= 1
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
        elif key == KEY_LEFT:
            if self.col > 0:
                self.col -= 1
            elif self.cur_line > 0:
                self.cur_line -= 1
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
                self.col = len(self.content[self.cur_line])
        elif key == KEY_RIGHT:
            if self.col < len(self.content[self.cur_line]):
                self.col += 1
            elif self.cur_line < self.total_lines - 1:
                self.cursor_down()
                self.col = 0
        elif key == KEY_HOME:
            ns = self.spaces(self.content[self.cur_line])
            self.col = ns if self.col != ns else 0
        elif key == KEY_END:
            self.col = len(self.content[self.cur_line])
        elif key == KEY_PGUP:
            self.cur_line -= self.height
        elif key == KEY_PGDN:
            self.cur_line += self.height
        elif key == KEY_FIND:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat, self.col)
                self.row = self.height >> 1
        elif key == KEY_FIND_AGAIN:
            if self.find_pattern:
                self.find_in_file(self.find_pattern, self.col + 1)
                self.row = self.height >> 1
        elif key == KEY_GOTO: ## goto line
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = self.height >> 1
                except:
                    pass
#ifndef BASIC
        elif key == KEY_MOUSE: ## Set Cursor
            if self.mouse_y < self.height:
                self.col = self.mouse_x + self.margin
                self.cur_line = self.mouse_y + self.top_line
            self.message = ' '
        elif key == KEY_SCRLUP: ##
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + self.height - 1)
                self.scroll_up(3)
        elif key == KEY_SCRLDN: ##
            if self.top_line + self.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scroll_down(3)
        elif key == KEY_TOGGLE: ## Toggle Autoindent/Statusline/Search case
            pat = self.line_edit("Case Sensitive Search %c, Autoindent %c, Tab Size %d, Write Tabs %c: " %
                  (self.case, self.autoindent, self.tab_size, self.write_tabs), "")
            try:
                res =  [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case       = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: self.autoindent = 'y' if res[1][0] == 'y' else 'n'
                if res[2]:
                    try: self.tab_size = int(res[2])
                    except: pass
                if res[3]: self.write_tabs = 'y' if res[3][0] == 'y' else 'n'
            except:
                pass
        elif key == KEY_FIRST: ## first line
            self.cur_line = 0
        elif key == KEY_LAST: ## last line
            self.cur_line = self.total_lines - 1
            self.row = self.height - 1 ## will be fixed if required
#endif
        else:
            return False
        return True

    def undo_add(self, lnum, text, key, span = 1):
        if self.undo_limit > 0 and (
           len(self.undo) == 0 or key == 0 or self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit: ## drop oldest undo
                del self.undo[0]
                self.sticky_c = "*"
            self.undo.append((lnum, span, text, key, self.col))

    def handle_edit_key(self, key): ## keys which change content
        l = self.content[self.cur_line]
        if key == KEY_ENTER:
            self.undo_add(self.cur_line, [l], 0, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if self.autoindent == "y": ## Autoindent
                ni = min(self.spaces(l), self.col)  ## query indentation
                r = self.content[self.cur_line].partition("\x23")[0].rstrip() ## \x23 == #
                if r and r[-1] == ':' and self.col >= len(r): ## look for : as the last non-space before comment
                    ni += self.tab_size
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
            self.changed = '*'
        elif key == KEY_BACKSPACE:
            if self.col > 0:
                self.undo_add(self.cur_line, [l], key)
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
                self.changed = '*'
#ifndef BASIC
            elif self.cur_line > 0: # at the start of a line, but not the first
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], 0)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += self.content.pop(self.cur_line)
                self.cur_line -= 1
                self.total_lines -= 1
                self.changed = '*'
#endif
        elif key == KEY_DELETE:
            if self.col < len(l):
                self.undo_add(self.cur_line, [l], key)
                l = l[:self.col] + l[self.col + 1:]
                self.content[self.cur_line] = l
                self.changed = '*'
            elif (self.cur_line + 1) < self.total_lines: ## test for last line
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], 0)
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
                self.changed = '*'
        elif key == KEY_TAB:
            self.undo_add(self.cur_line, [l], key)
            ni = self.tab_size - self.col % self.tab_size ## determine spaces to add
            self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
            self.col += ni
            self.changed = '*'
        elif key == KEY_BACKTAB:
            self.undo_add(self.cur_line, [l], key)
            ni = min((self.col - 1) % self.tab_size + 1, self.spaces(l, self.col)) ## determine spaces to drop
            self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
            self.col -= ni
            self.changed = '*'
#ifndef BASIC
        elif key == KEY_REPLC:
            count = 0
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("Replace with: ", self.replc_pattern)
                if rpat != None:
                    self.replc_pattern = rpat
                    q = ''
                    while True:
                        ni = self.find_in_file(pat, self.col)
                        if ni:
                            if q != 'a':
                                self.message = "Replace (yes/No/all/quit) ? "
                                self.display_window()
                                key = self.get_input()  ## Get Char of Fct.
                                q = chr(key).lower()
                            if q == 'q' or key == KEY_QUIT:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], 0)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                                self.changed = '*'
                            else: ## everything else is no
                                self.col += 1
                        else:
                            break
                    self.message = "'%s' replaced %d times" % (pat, count)
        elif key == KEY_GET:
            fname = self.line_edit("Insert File: ", "")
            if fname:
                (content, self.message) = self.get_file(fname)
                if content:
                    self.undo_add(self.cur_line, None, 0, -len(content))
                    self.content[self.cur_line:self.cur_line] = content
                    self.total_lines = len(self.content)
                    self.changed = "*"
#endif
        elif key == KEY_YANK:  # delete line into buffer
            self.undo_add(self.cur_line, [l], 0, 0)
            if key == self.lastkey: # yank series?
                self.yank_buffer.append(l) # add line
            else:
                self.yank_buffer = [l]
            if self.total_lines > 1: ## not a single line
                del self.content[self.cur_line]
                self.total_lines -= 1
                if self.cur_line  >= self.total_lines: ## on last line move pointer
                    self.cur_line -= 1
            else: ## line is kept but wiped
                self.content[self.cur_line] = ''
            self.changed = '*'
        elif key == KEY_DUP:  # copy line into buffer and go down one line
            if key == self.lastkey: # yank series?
                self.yank_buffer.append(l) # add line
            else:
                self.yank_buffer = [l]
            self.cursor_down()
        elif key == KEY_ZAP: ## insert buffer
            if self.yank_buffer:
                self.undo_add(self.cur_line, None, 0, -len(self.yank_buffer))
                self.content[self.cur_line:self.cur_line] = self.yank_buffer # insert lines
                self.total_lines += len(self.yank_buffer)
                self.changed = '*'
        elif key == KEY_WRITE:
            fname = self.fname
            if fname == None:
                fname = ""
            fname = self.line_edit("File Name: ", fname)
            if fname:
                try:
                    with open(fname, "w") as f:
                        for l in self.content:
#ifndef BASIC
                            if self.write_tabs == 'y':
                                f.write(self.packtabs(l) + '\n')
                            else:
#endif
                                f.write(l + '\n')
                    self.changed = " " ## clear change flag
                    self.sticky_c = " " ## clear undo
                    del self.undo[:]
                    self.fname = fname ## remember (new) name
                except Exception as err:
                    self.message = 'Could not save %s, Error: %s' % (fname, err)
        elif key == KEY_UNDO:
            if len(self.undo) > 0:
                action = self.undo.pop(-1) ## get action from stack
                self.cur_line = action[0]
                self.col = action[4]
                if action[1] >= 0: ## insert or replace line
                    if action[0] < self.total_lines:
                        self.content[self.cur_line:self.cur_line + action[1]] = action[2] # insert lines
                    else:
                        self.content += action[2]
                else: ## delete lines
                    del self.content[self.cur_line : self.cur_line - action[1]]
                self.total_lines = len(self.content) ## brute force
                if len(self.undo) == 0: ## test changed flag
                    self.changed = self.sticky_c
#ifdef BASIC                    
        elif key < 0x20:
            self.message = "Sorry, command not supported"
#endif
        elif key >= 0x20: ## character to be added
            self.undo_add(self.cur_line, [l], 0x20 if key == 0x20 else 0x41)
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
            self.changed = '*'

    def edit_loop(self): ## main editing loop

        if len(self.content) == 0: ## check for empty content
            self.content = [""]
        self.total_lines = len(self.content)
        self.set_screen_parms()
#ifndef BASIC
        self.mouse_reporting(True) ## enable mouse reporting
#endif

        while True:
            self.display_window()  ## Update & display window
            key = self.get_input()  ## Get Char of Fct-key code
            self.message = '' ## clear message

            if key == KEY_QUIT:
                if self.changed != ' ':
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
## Do not leave cursor in the middle of screen
#ifndef BASIC
                self.mouse_reporting(False) ## disable mouse reporting, enable scrolling
#endif
                self.scroll_region(0)
                self.goto(self.height, 0)
                self.clear_to_eol()
                return None
            elif key == KEY_REDRAW:
                self.set_screen_parms()
                self.row = min(self.height - 1, self.row)
#ifdef LINUX
                if sys.platform in ("linux", "darwin") and sys.implementation.name == "cpython":
                    signal.signal(signal.SIGWINCH, Editor.signal_handler)
#endif
                if sys.implementation.name == "micropython":
                    gc.collect()
                    self.message = "%d Bytes Memory available" % gc.mem_free()
            elif  self.handle_cursor_keys(key):
                pass
            else: self.handle_edit_key(key)
            self.lastkey = key
## expandtabs: hopefully sometimes replaced by the built-in function
    @staticmethod
    def expandtabs(s):
        from _io import StringIO
        if '\t' in s:
            sb = StringIO()
            pos = 0
            for c in s:
                if c == '\t': ## tab is seen
                    sb.write(" " * (8 - pos % 8)) ## replace by space
                    pos += 8 - pos % 8
                else:
                    sb.write(c)
                    pos += 1
            return sb.getvalue()
        else:
            return s
## packtabs: replace sequence of space by tab
#ifndef BASIC
    @staticmethod
    def packtabs(s):
        from _io import StringIO
        sb = StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if c != cr: ## Spaces at the end of a section
                sb.write(cr + "\t") ## replace by tab
            else:
                sb.write(c)
        return sb.getvalue()
#endif
    @staticmethod
    def get_file(fname):
        try:
#ifdef LINUX
            if sys.implementation.name == "cpython":
                with open(fname, errors="ignore") as f:
                    content = f.readlines()
            else:
#endif
                with open(fname) as f:
                    content = f.readlines()
        except Exception as err:
            message = 'Could not load %s, Error: %s' % (fname, err)
            return (None, message)
        for i in range(len(content)):  ## strip and convert
            content[i] = Editor.expandtabs(content[i].rstrip('\r\n\t '))
        return (content, "")

def pye(content = None, tab_size = 4, undo = 50, device = 0, baud = 115200):
## prepare content
    e = Editor(tab_size, undo)
    if type(content) == str and content: ## String = non-empty Filename
        e.fname = content
        (e.content, e.message) = e.get_file(e.fname)
        if e.content == None:  ## Error reading file
            print (e.message)
            return
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        ## non-empty list of strings -> edit
        e.content = content
## edit
    e.init_tty(device, baud)
    e.edit_loop()
    e.deinit_tty()
## clean-up
    content = e.content if (e.fname == None) else e.fname
    return content

#ifdef LINUX
if __name__ == "__main__":
    if sys.platform in ("linux", "darwin"):
        import stat
        fd_tty = 0
        if len(sys.argv) > 1:
            name = sys.argv[1]
        else:
            name = ""
            if sys.implementation.name == "cpython":
                mode = os.fstat(0).st_mode
                if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
                    name = sys.stdin.readlines()
                    os.close(0) ## close and repopen /dev/tty
                    fd_tty = os.open("/dev/tty", os.O_RDONLY) ## memorized, if new fd
                    for i in range(len(name)):  ## strip and convert
                        name[i] = Editor.expandtabs(name[i].rstrip('\r\n\t '))
        pye(name, undo = 500, device=fd_tty)
    else:
        print ("\nSorry, this OS is not supported (yet)")
#endif
