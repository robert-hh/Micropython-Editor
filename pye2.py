##
## Small python text editor based on the
## Very simple VT100 terminal text editor widget
## Copyright (c) 2015 Paul Sokolovsky (initial code)
## Copyright (c) 2015 Robert Hammelrath (additional code)
## Distributed under MIT License
## Changes:
## - Ported the code to PyBoard and Wipy (still runs on Linux or Darwin)
##   It uses VCP_USB on Pyboard and sys.stdin on WiPy, or UART, if selected.
## - changed read keyboard function to comply with char-by-char input
## - added support for TAB, BACKTAB, SAVE, DEL and Backspace joining lines,
##   Find, Replace, Goto Line, UNDO, GET file, Auto-Indent, Set Flags,
##   Copy/Delete & Paste, Indent, Un-Indent
## - Added mouse support for pointing and scrolling (not WiPy)
## - handling tab (0x09) on reading & writing files,
## - Added a status line and single line prompts for
##   Quit, Save, Find, Replace, Flags and Goto
## - moved main into a function with some optional parameters
## - Added multi-file support
##
#ifndef BASIC
#define REPLACE 1
#define BRACKET 1
#define INDENT 1
##define MOUSE 1
#endif
import sys, gc
if sys.platform in ("linux", "darwin"):
    import os, signal, tty, termios
    is_linux = True
else:
    is_linux = False

if sys.implementation.name == "micropython":
    is_micropython = True
    from uio import StringIO
    from ure import compile as re_compile
else:
    is_micropython = False
    const = lambda x: x
    from _io import StringIO
    from re import compile as re_compile

PYE_VERSION   = " V2.27 "
KEY_NONE      = const(0x00)
KEY_UP        = const(0x0b)
KEY_DOWN      = const(0x0d)
KEY_LEFT      = const(0x1f)
KEY_RIGHT     = const(0x1e)
KEY_HOME      = const(0x10)
KEY_END       = const(0x03)
KEY_PGUP      = const(0xfff1)
KEY_PGDN      = const(0xfff2)
KEY_QUIT      = const(0x11)
KEY_ENTER     = const(0x0a)
KEY_BACKSPACE = const(0x08)
KEY_DELETE    = const(0x7f)
KEY_WRITE     = const(0x13)
KEY_TAB       = const(0x09)
KEY_BACKTAB   = const(0x15)
KEY_FIND      = const(0x06)
KEY_GOTO      = const(0x07)
KEY_MOUSE     = const(0x1b)
KEY_SCRLUP    = const(0x1c)
KEY_SCRLDN    = const(0x1d)
KEY_FIND_AGAIN= const(0x0e)
KEY_REDRAW    = const(0x05)
KEY_UNDO      = const(0x1a)
KEY_YANK      = const(0x18)
KEY_ZAP       = const(0x16)
KEY_DUP       = const(0x04)
KEY_FIRST     = const(0x14)
KEY_LAST      = const(0x02)
KEY_REPLC     = const(0x12)
KEY_TOGGLE    = const(0x01)
KEY_GET       = const(0x0f)
KEY_MARK      = const(0x0c)
KEY_NEXT      = const(0x17)
KEY_COMMENT   = const(0xfffc)
KEY_MATCH     = const(0xfffd)
KEY_INDENT    = const(0xfffe)
KEY_UNDENT    = const(0xffff)

class Editor:

    KEYMAP = { ## Gets lengthy
    "\x1b[A" : KEY_UP,
    "\x1b[B" : KEY_DOWN,
    "\x1b[D" : KEY_LEFT,
    "\x1b[C" : KEY_RIGHT,
    "\x1b[H" : KEY_HOME, ## in Linux Terminal
    "\x1bOH" : KEY_HOME, ## Picocom, Minicom
    "\x1b[1~": KEY_HOME, ## Putty
    "\x1b[F" : KEY_END,  ## Linux Terminal
    "\x1bOF" : KEY_END,  ## Picocom, Minicom
    "\x1b[4~": KEY_END,  ## Putty
    "\x1b[5~": KEY_PGUP,
    "\x1b[6~": KEY_PGDN,
    "\x03"   : KEY_DUP, ## Ctrl-C
    "\r"     : KEY_ENTER,
    "\x7f"   : KEY_BACKSPACE, ## Ctrl-? (127)
    "\x1b[3~": KEY_DELETE,
    "\x1b[Z" : KEY_BACKTAB, ## Shift Tab
    "\x19"   : KEY_YANK, ## Ctrl-Y alias to Ctrl-X
    "\x08"   : KEY_REPLC, ## Ctrl-H
    "\x12"   : KEY_REPLC, ## Ctrl-R
    "\x11"   : KEY_QUIT, ## Ctrl-Q
    "\x1c"   : KEY_QUIT, ## Ctrl-Q
    "\n"     : KEY_ENTER,
    "\x13"   : KEY_WRITE,  ## Ctrl-S
    "\x06"   : KEY_FIND, ## Ctrl-F
    "\x0e"   : KEY_FIND_AGAIN, ## Ctrl-N
    "\x07"   : KEY_GOTO, ##  Ctrl-G
    "\x05"   : KEY_REDRAW, ## Ctrl-E
    "\x1a"   : KEY_UNDO, ## Ctrl-Z
    "\x09"   : KEY_TAB,
    "\x15"   : KEY_BACKTAB, ## Ctrl-U
    "\x18"   : KEY_YANK, ## Ctrl-X
    "\x16"   : KEY_ZAP, ## Ctrl-V
    "\x04"   : KEY_DUP, ## Ctrl-D
    "\x0c"   : KEY_MARK, ## Ctrl-L
    "\x00"   : KEY_MARK, ## Ctrl-Space
    "\x14"   : KEY_FIRST, ## Ctrl-T
    "\x02"   : KEY_LAST,  ## Ctrl-B
    "\x01"   : KEY_TOGGLE, ## Ctrl-A
    "\x17"   : KEY_NEXT, ## Ctrl-W
    "\x0f"   : KEY_GET, ## Ctrl-O
    "\x10"   : KEY_COMMENT, ## Ctrl-P
## other keys
    "\x1b[1;5H": KEY_FIRST, ## Ctrl-Home
    "\x1b[1;5F": KEY_LAST, ## Ctrl-End
    "\x1b[3;5~": KEY_YANK, ## Ctrl-Del
    "\x0b"   : KEY_MATCH,## Ctrl-K
    "\x1b[M" : KEY_MOUSE,
    }
## symbols that are shared between instances of Editor
    yank_buffer = []
    find_pattern = ""
    case = "n"
    autoindent = "y"
    replc_pattern = ""
    comment_char = "\x23 "

    def __init__(self, tab_size, undo_limit):
        self.top_line = self.cur_line = self.row = self.col = self.margin = 0
        self.tab_size = tab_size
        self.changed = ""
        self.message = self.fname = ""
        self.content = [""]
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
        self.undo_zero = 0
        self.mark = None
        self.straight = "y"
        self.write_tabs = "n"
#ifdef LINUX
    if is_linux:

        def wr(self,s):
            os.write(1, s.encode("utf-8"))

        def rd(self):
            while True:
                try: ## WINCH causes interrupt
                    c = os.read(self.sdev,1)
                    flag = c[0]
                    while (flag & 0xc0) == 0xc0:  ## utf-8 char collection
                        c += os.read(self.sdev,1)
                        flag <<= 1
                    return c.decode("UTF-8")
                except:
                    if Editor.winch: ## simulate REDRAW key
                        Editor.winch = False
                        return '\x05'

        @staticmethod
        def init_tty(device):
            Editor.org_termios = termios.tcgetattr(device)
            tty.setraw(device)
            Editor.sdev = device
            Editor.winch = False

        @staticmethod
        def deinit_tty():
            termios.tcsetattr(Editor.sdev, termios.TCSANOW, Editor.org_termios)

        @staticmethod
        def signal_handler(sig, frame):
            signal.signal(signal.SIGWINCH, signal.SIG_IGN)
            Editor.winch = True
            return True
#endif
#if defined(MICROPYTHON)
    if is_micropython and not is_linux:

        def wr(self, s):
            sys.stdout.write(s)

        def rd(self):
            return sys.stdin.read(1)

        @staticmethod
        def init_tty(device):
            try:
                from micropython import kbd_intr
                kbd_intr(-1)
            except ImportError:
                pass

        @staticmethod
        def deinit_tty():
            try:
                from micropython import kbd_intr
                kbd_intr(3)
            except ImportError:
                pass
#endif
    def goto(self, row, col):
        self.wr("\x1b[{};{}H".format(row + 1, col + 1))

    def clear_to_eol(self):
        self.wr("\x1b[0K")

    def cursor(self, onoff):
        self.wr("\x1b[?25h" if onoff else "\x1b[?25l")

    def hilite(self, mode):
        if mode == 1: ## used for the status line
            self.wr("\x1b[1;47m")
        elif mode == 2: ## used for the marked area
            self.wr("\x1b[43m")
        else:         ## plain text
            self.wr("\x1b[0m")

    def mouse_reporting(self, onoff):
        self.wr('\x1b[?9h' if onoff else '\x1b[?9l') ## enable/disable mouse reporting

    def scroll_region(self, stop):
        self.wr('\x1b[1;{}r'.format(stop) if stop else '\x1b[r') ## set scrolling range

    def scroll_up(self, scrolling):
        Editor.scrbuf[scrolling:] = Editor.scrbuf[:-scrolling]
        Editor.scrbuf[:scrolling] = [''] * scrolling
        self.goto(0, 0)
        self.wr("\x1bM" * scrolling)

    def scroll_down(self, scrolling):
        Editor.scrbuf[:-scrolling] = Editor.scrbuf[scrolling:]
        Editor.scrbuf[-scrolling:] = [''] * scrolling
        self.goto(Editor.height - 1, 0)
        self.wr("\x1bD" * scrolling)

    def get_screen_size(self):
        self.wr('\x1b[999;999H\x1b[6n')
        pos = ''
        char = self.rd() ## expect ESC[yyy;xxxR
        while char != 'R':
            pos += char
            char = self.rd()
        return [int(i, 10) for i in pos.lstrip("\n\x1b[").split(';')]

    def redraw(self, flag):
        self.cursor(False)
        Editor.height, Editor.width = self.get_screen_size()
        Editor.height -= 1
        Editor.scrbuf = [(False,"\x00")] * Editor.height ## force delete
        self.row = min(Editor.height - 1, self.row)
        self.scroll_region(Editor.height)
        self.mouse_reporting(True) ## enable mouse reporting
        if is_linux and not is_micropython:
            signal.signal(signal.SIGWINCH, Editor.signal_handler)
        self.message = PYE_VERSION
        if is_micropython:
            gc.collect()
            if flag:
                self.message += "{} Bytes Memory available".format(gc.mem_free())

    def get_input(self):  ## read from interface/keyboard one byte each and match against function keys
        while True:
            in_buffer = self.rd()
            if in_buffer == '\x1b': ## starting with ESC, must be fct
                while True:
                    in_buffer += self.rd()
                    c = in_buffer[-1]
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
            if in_buffer in self.KEYMAP:
                c = self.KEYMAP[in_buffer]
                if c != KEY_MOUSE:
                    return c, ""
                else: ## special for mice
                    mouse_fct = ord((self.rd())) ## read 3 more chars
                    mouse_x = ord(self.rd()) - 33
                    mouse_y = ord(self.rd()) - 33
                    if mouse_fct == 0x61:
                        return KEY_SCRLDN, ""
                    elif mouse_fct == 0x60:
                        return KEY_SCRLUP, ""
                    else:
                        return KEY_MOUSE, [mouse_x, mouse_y, mouse_fct] ## set the cursor
            elif ord(in_buffer[0]) >= 32:
                return KEY_NONE, in_buffer

    def display_window(self): ## Update window and status line
## Force cur_line and col to be in the reasonable bounds
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
## Check if Column is out of view, and align margin if needed
        if self.straight != "y":
            self.col = min(self.col, len(self.content[self.cur_line]))
        if self.col <  0:
            self.col = 0
        if self.col >= Editor.width + self.margin:
            self.margin = self.col - Editor.width + (Editor.width >> 2)
        elif self.col < self.margin:
            self.margin = max(self.col - (Editor.width >> 2), 0)
## if cur_line is out of view, align top_line to the given row
        if not (self.top_line <= self.cur_line < self.top_line + Editor.height): # Visible?
            self.top_line = max(self.cur_line - self.row, 0)
## in any case, align row to top_line and cur_line
        self.row = self.cur_line - self.top_line
## update_screen
        self.cursor(False)
        i = self.top_line
        for c in range(Editor.height):
            if i == self.total_lines: ## at empty bottom screen part
                if Editor.scrbuf[c] != (False,''):
                    self.goto(c, 0)
                    self.clear_to_eol()
                    Editor.scrbuf[c] = (False,'')
            else:
                l = (self.mark is not None and (
                    (min(self.mark, self.cur_line) <= i <= max(self.cur_line, self.mark))),
                     self.content[i][self.margin:self.margin + Editor.width])
                if l != Editor.scrbuf[c]: ## line changed, print it
                    self.goto(c, 0)
                    if l[0]:
                        self.hilite(2)
                    self.wr(l[1])
                    if len(l[1]) < Editor.width:
                        self.clear_to_eol()
                    if l[0]:
                        self.hilite(0)
                    Editor.scrbuf[c] = l
                i += 1
## display Status-Line
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr("{}{} Row: {}/{} Col: {}  {}".format(
            self.changed, self.fname, self.cur_line + 1, self.total_lines,
            self.col + 1, self.message)[:self.width - 1])
        self.clear_to_eol() ## once moved up for mate/xfce4-terminal issue with scroll region
        self.hilite(0)
        self.goto(self.row, self.col - self.margin)
        self.cursor(True)

    def spaces(self, line, pos = None): ## count spaces
        return (len(line) - len(line.lstrip(" ")) if pos is None else ## at line start
                len(line[:pos]) - len(line[:pos].rstrip(" ")))

    def line_range(self):
        return ((self.mark, self.cur_line + 1) if self.mark < self.cur_line else
                (self.cur_line, self.mark + 1))

    def line_edit(self, prompt, default, zap=None):  ## better one: added cursor keys and backsp, delete
        push_msg = lambda msg: self.wr(msg + "\b" * len(msg)) ## Write a message and move cursor back
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        pos = len(res)
        while True:
            key, char = self.get_input()  ## Get Char of Fct.
            if key == KEY_NONE: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + char + res[pos:]
                    self.wr(res[pos])
                    pos += len(char)
                    push_msg(res[pos:]) ## update tail
            elif key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(0)
                return res
            elif key in (KEY_QUIT, KEY_DUP): ## Abort
                self.hilite(0)
                return None
            elif key == KEY_LEFT:
                if pos > 0:
                    self.wr("\b")
                    pos -= 1
            elif key == KEY_RIGHT:
                if pos < len(res):
                    self.wr(res[pos])
                    pos += 1
            elif key == KEY_DELETE: ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ') ## update tail
            elif key == KEY_BACKSPACE: ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    push_msg(res[pos:] + ' ') ## update tail
            elif key == KEY_HOME:
                self.wr("\b" * pos)
                pos = 0
            elif key == KEY_END:
                self.wr(res[pos:])
                pos = len(res)
            elif key == KEY_ZAP: ## Get from content
                char = self.getsymbol(self.content[self.cur_line], self.col, zap)
                if char is not None:
                    self.wr('\b' * pos + ' ' * len(res) + '\b' * len(res))
                    res = char
                    self.wr(res)
                    pos = len(res)

    def getsymbol(self, s, pos, zap):
        if pos < len(s) and zap is not None:
            issymbol = lambda c: c.isalpha() or c.isdigit() or c in zap
            start = stop = pos
            while start >= 0 and issymbol(s[start]):
                start -= 1
            while stop < len(s) and issymbol(s[stop]):
                stop += 1
            return s[start+1:stop]
        else:
            return None

## This is the regex version of find.
    def find_in_file(self, pattern, col, end):
        if is_micropython:
            from ure import compile as re_compile
        else:
            from re import compile as re_compile

        Editor.find_pattern = pattern ## remember it
        if Editor.case != "y":
            pattern = pattern.lower()
        try:
            rex = re_compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return None
        start = self.cur_line
        if (col > len(self.content[start]) or   # After EOL
            (pattern[0] == '^' and col != 0)):  # or anchored and not at BOL
            start, col = start + 1, 0           # Skip to the next line
        for line in range(start, end):
            l = self.content[line][col:]
            if Editor.case != "y":
                l = l.lower()
            match = rex.search(l)
            if match: # Bingo
                self.cur_line = line
## Instead of match.span, a simple find has to be performed to get the cursor position.
## And '$' has to be treated separately, so look for a true EOL match first
                if pattern[-1:] == "$" and match.group(0)[-1:] != "$":
                    self.col = col + len(l) - len(match.group(0))
                else:
                    self.col = col + l.find(match.group(0))
                return len(match.group(0))
            col = 0
        else:
            self.message = pattern + " not found (again)"
            return None

    def undo_add(self, lnum, text, key, span = 1):
        self.changed = '*'
        if self.undo_limit > 0 and (
           len(self.undo) == 0 or key == KEY_NONE or self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit: ## drop oldest undo, if full
                del self.undo[0]
                self.undo_zero -= 1
            self.undo.append([lnum, span, text, key, self.col])

    def delete_lines(self, yank): ## copy marked lines (opt) and delete them
        lrange = self.line_range()
        if yank:
            Editor.yank_buffer = self.content[lrange[0]:lrange[1]]
        self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_NONE, 0) ## undo inserts
        del self.content[lrange[0]:lrange[1]]
        if self.content == []: ## if all was wiped
            self.content = [""] ## add a line
            self.undo[-1][1] = 1 ## tell undo to overwrite this single line
        self.total_lines = len(self.content)
        self.cur_line = lrange[0]
        self.mark = None ## unset line mark

    def handle_edit_keys(self, key, char): ## keys which edit the buffer
        l = self.content[self.cur_line]
        jut = self.col - len(l) ## <0: before text end, = 0 at text end, >0 beyond text end
        if key == KEY_NONE: ## character to be added
            self.mark = None
            self.undo_add(self.cur_line, [l], 0x20 if char == " " else 0x41)
## ' ' * jut is an empty string for jut <= 0
            if jut > 0:
                self.content[self.cur_line] = l[:self.col] + ' ' * jut + char
            else:
                self.content[self.cur_line] = l[:self.col] + char + l[self.col:]
            self.col += len(char)
        elif key == KEY_DOWN:
            if self.cur_line < self.total_lines - 1:
                self.cur_line += 1
                if self.cur_line == self.top_line + Editor.height:
                    self.scroll_down(1)
        elif key == KEY_UP:
            if self.cur_line > 0:
                self.cur_line -= 1
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
        elif key == KEY_LEFT:
            if self.col == 0 and self.cur_line > 0:
                self.cur_line -= 1
                self.col = len(self.content[self.cur_line])
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
            else:
                self.col -= 1
        elif key == KEY_RIGHT:
            if self.straight != "y" and self.col >= len(l) and self.cur_line < self.total_lines - 1:
                self.col = 0
                self.cur_line += 1
                if self.cur_line == self.top_line + Editor.height:
                    self.scroll_down(1)
            else:
                self.col += 1
        elif key == KEY_DELETE:
            if self.mark is not None:
                self.delete_lines(False)
            elif self.col < len(l):
                self.undo_add(self.cur_line, [l], KEY_DELETE)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines: ## test for last line
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], KEY_NONE)
                self.content[self.cur_line] = l + ' ' * jut + (
                    self.content.pop(self.cur_line + 1).lstrip()
                    if Editor.autoindent == "y" and self.col > 0 else
                    self.content.pop(self.cur_line + 1))
                self.total_lines -= 1
        elif key == KEY_BACKSPACE:
            if self.mark is not None:
                self.delete_lines(False)
            elif self.col > 0:
                if jut <= 0: ## if on solid ground
                    self.undo_add(self.cur_line, [l], KEY_BACKSPACE)
                    self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
            elif self.cur_line > 0: # at the start of a line, but not the first
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], KEY_NONE)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += self.content.pop(self.cur_line)
                self.cur_line -= 1
                self.total_lines -= 1
        elif key == KEY_HOME:
            ni = self.spaces(l)
            self.col = ni if self.col != ni else 0
        elif key == KEY_END:
            ni = len(l.split(Editor.comment_char.strip())[0].rstrip())
            ns = self.spaces(l)
            self.col = ni if self.col != ni and ni > ns else len(l)
        elif key == KEY_PGUP:
            self.cur_line -= Editor.height
        elif key == KEY_PGDN:
            self.cur_line += Editor.height
        elif key == KEY_FIND:
            pat = self.line_edit("Find: ", Editor.find_pattern, "_")
            if pat:
                self.find_in_file(pat, self.col, self.total_lines)
                self.row = Editor.height >> 1
        elif key == KEY_FIND_AGAIN:
            if Editor.find_pattern:
                self.find_in_file(Editor.find_pattern, self.col + 1, self.total_lines)
                self.row = Editor.height >> 1
        elif key == KEY_GOTO: ## goto line
            line = self.line_edit("Goto Line: ", "")
            if line:
                self.cur_line = int(line) - 1
                self.row = Editor.height >> 1
        elif key == KEY_FIRST: ## first line
            self.cur_line = 0
        elif key == KEY_LAST: ## last line
            self.cur_line = self.total_lines - 1
            self.row = Editor.height - 1 ## will be fixed if required
        elif key == KEY_TOGGLE: ## Toggle Autoindent/Statusline/Search case
            pat = self.line_edit("Autoindent {}, Search Case {}, Straight Cursor {}"
            ", Tabsize {}, Comment {}, Tabwrite {}: ".format(Editor.autoindent, Editor.case,
            self.straight, self.tab_size, Editor.comment_char, self.write_tabs), "")
            try:
                res =  [i.lstrip().lower() for i in pat.split(",")]
                if res[0]: Editor.autoindent = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: Editor.case     = 'y' if res[1][0] == 'y' else 'n'
                if res[2]: self.straight   = 'y' if res[2][0] == 'y' else 'n'
                if res[3]: self.tab_size   = int(res[3])
                if res[4]: Editor.comment_char = res[4]
                if res[5]: self.write_tabs = 'y' if res[5][0] == 'y' else 'n'
            except:
                pass
        elif key == KEY_MOUSE: ## Set Cursor
            if char[1] < Editor.height:
                self.col = char[0] + self.margin
                self.cur_line = char[1] + self.top_line
                if char[2] in (0x22, 0x30): ## Right/Ctrl button on Mouse
                    self.mark = self.cur_line if self.mark is None else None
        elif key == KEY_SCRLUP: ##
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + Editor.height - 1)
                self.scroll_up(3)
        elif key == KEY_SCRLDN: ##
            if self.top_line + Editor.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scroll_down(3)
        elif key == KEY_MATCH:
            if self.col < len(l): ## ony within text
                opening = "([{<"
                closing = ")]}>"
                level = 0
                pos = self.col
                srch = l[pos]
                i = opening.find(srch)
                if i >= 0: ## at opening bracket, look forward
                    pos += 1
                    match = closing[i]
                    for i in range(self.cur_line, self.total_lines):
                        for c in range(pos, len(self.content[i])):
                            if self.content[i][c] == match:
                                if level == 0: ## match found
                                    self.cur_line, self.col  = i, c
                                    return True  ## return here instead of ml-breaking
                                else:
                                    level -= 1
                            elif self.content[i][c] == srch:
                                level += 1
                        pos = 0 ## next line starts at 0
                else:
                    i = closing.find(srch)
                    if i >= 0: ## at closing bracket, look back
                        pos -= 1
                        match = opening[i]
                        for i in range(self.cur_line, -1, -1):
                            for c in range(pos, -1, -1):
                                if self.content[i][c] == match:
                                    if level == 0: ## match found
                                        self.cur_line, self.col  = i, c
                                        return True ## return here instead of ml-breaking
                                    else:
                                        level -= 1
                                elif self.content[i][c] == srch:
                                    level += 1
                            if i > 0: ## prev line, if any, starts at the end
                                pos = len(self.content[i - 1]) - 1
        elif key == KEY_MARK:
            self.mark = self.cur_line if self.mark is None else None
        elif key == KEY_ENTER:
            self.mark = None
            self.undo_add(self.cur_line, [l], KEY_NONE, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if Editor.autoindent == "y": ## Autoindent
                ni = min(self.spaces(l), self.col)  ## query indentation
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == KEY_TAB:
            if self.mark is None:
                ni = self.tab_size - self.col % self.tab_size ## determine spaces to add
                self.undo_add(self.cur_line, [l], KEY_TAB)
                if jut < 0:
                    self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
                self.col += ni
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_INDENT, lrange[1] - lrange[0]) ## undo replaces
                for i in range(lrange[0],lrange[1]):
                    if len(self.content[i]) > 0:
                        self.content[i] = ' ' * (self.tab_size - self.spaces(self.content[i]) % self.tab_size) + self.content[i]
        elif key == KEY_BACKTAB:
            if self.mark is None:
                ni = (self.col - 1) % self.tab_size + 1
                if jut <= 0:
                    ni = min(ni, self.spaces(l, self.col)) ## determine spaces to drop
                    if ni > 0:
                        self.undo_add(self.cur_line, [l], KEY_BACKTAB)
                        self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                        self.col -= ni
                else:
                    self.col -= min(ni, jut)
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_UNDENT, lrange[1] - lrange[0]) ## undo replaces
                for i in range(lrange[0],lrange[1]):
                    ns = self.spaces(self.content[i])
                    if ns > 0:
                        self.content[i] = self.content[i][(ns - 1) % self.tab_size + 1:]
        elif key == KEY_REPLC:
            count = 0
            pat = self.line_edit("Replace: ", Editor.find_pattern, "_")
            if pat:
                rpat = self.line_edit("With: ", Editor.replc_pattern, "_")
                if rpat is not None: ## start with setting up loop parameters
                    Editor.replc_pattern = rpat
                    q = ''
                    cur_line, cur_col = self.cur_line, self.col ## remember pos
                    if self.mark is not None: ## Replace in Marked area
                        (self.cur_line, end_line) = self.line_range()
                        self.col = 0
                    else: ## replace from cur_line to end
                        end_line = self.total_lines
                    self.message = "Replace (yes/No/all/quit) ? "
                    while True: ## and go
                        ni = self.find_in_file(pat, self.col, end_line)
                        if ni is not None: ## Pattern found
                            if q != 'a':
                                self.display_window()
                                key, char = self.get_input()  ## Get Char of Fct.
                                q = char.lower()
                            if q == 'q' or key == KEY_QUIT:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], KEY_NONE)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat) + (ni == 0) # ugly but short
                                count += 1
                            else: ## everything else is no
                                 self.col += 1
                        else: ## not found, quit
                            break
                    self.cur_line, self.col = cur_line, cur_col ## restore pos
                    self.message = "'{}' replaced {} times".format(pat, count)
        elif key == KEY_YANK:  # delete line or line(s) into buffer
            if self.mark is not None:
                self.delete_lines(True)
        elif key == KEY_DUP:  # copy line(s) into buffer
            if self.mark is not None:
                lrange = self.line_range()
                Editor.yank_buffer = self.content[lrange[0]:lrange[1]]
                self.mark = None
        elif key == KEY_ZAP: ## insert buffer
            if Editor.yank_buffer:
                if self.mark is not None:
                    self.delete_lines(False)
                self.undo_add(self.cur_line, None, KEY_NONE, -len(Editor.yank_buffer))
                self.content[self.cur_line:self.cur_line] = Editor.yank_buffer # insert lines
                self.total_lines += len(Editor.yank_buffer)
        elif key == KEY_WRITE:
            fname = self.line_edit("Save File: ", self.fname)
            if fname:
                self.put_file(fname)
                self.changed = '' ## clear change flag
                self.undo_zero = len(self.undo) ## remember state
                self.fname = fname ## remember (new) name
        elif key == KEY_UNDO:
            if len(self.undo) > 0:
                action = self.undo.pop(-1) ## get action from stack
                if not action[3] in (KEY_INDENT, KEY_UNDENT):
                    self.cur_line = action[0] ## wrong for Bkspc of BOL
                self.col = action[4]
                if action[1] >= 0: ## insert or replace line
                    if action[0] < self.total_lines:
                        self.content[action[0]:action[0] + action[1]] = action[2] # insert lines
                    else:
                        self.content += action[2]
                else: ## delete lines
                    del self.content[action[0]:action[0] - action[1]]
                self.total_lines = len(self.content) ## brute force
                if len(self.undo) == self.undo_zero:
                    self.changed = ''
                self.mark = None
        elif key == KEY_COMMENT:
            if self.mark is None:
                lrange = (self.cur_line, self.cur_line + 1)
            else:
                lrange = self.line_range()
            self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_COMMENT, lrange[1] - lrange[0]) ## undo replaces
            ni = len(Editor.comment_char)
            for i in range(lrange[0],lrange[1]):
                ns = self.spaces(self.content[i])
                if self.content[i][ns:ns + ni] == Editor.comment_char:
                    self.content[i] = ns * " " + self.content[i][ns + ni:]
                else:
                    self.content[i] = ns * " " + Editor.comment_char + self.content[i][ns:]
        elif key == KEY_REDRAW:
            self.redraw(True)

    def edit_loop(self): ## main editing loop
        if not self.content: ## ensure content
            self.content = [""]
        self.total_lines = len(self.content)
        self.redraw(self.message == "")

        while True:
            self.display_window()  ## Update & display window
            key, char = self.get_input()  ## Get Char of Fct-key code
            self.message = '' ## clear message

            if key == KEY_QUIT:
                if self.changed:
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                self.scroll_region(0)
                self.mouse_reporting(False) ## disable mouse reporting
                self.goto(Editor.height, 0)
                self.clear_to_eol()
                self.undo = []
                return key
            elif key in (KEY_NEXT, KEY_GET):
                return key
            else:
                self.handle_edit_keys(key, char)

## packtabs: replace sequence of space by tab
    def packtabs(self, s):
        sb = StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if (len(c) - len(cr)) > 1:
                sb.write(cr + "\t") ## Spaces at the end of a section
            else:
                sb.write(c)
        return sb.getvalue()

## Read file into content
    def get_file(self, fname):
        from os import listdir, stat
        if fname:
            self.fname = fname
            if fname in ('.', '..') or (stat(fname)[0] & 0x4000): ## Dir
                self.content = ["Directory '{}'".format(fname), ""] + sorted(listdir(fname))
            else:
                if is_micropython:
                    with open(fname) as f:
                        self.content = f.readlines()
                else:
                    with open(fname, errors="ignore") as f:
                        self.content = f.readlines()
                tabs = False
                for i, l in enumerate(self.content):
                    self.content[i], tf = expandtabs(l.rstrip('\r\n\t '))
                    tabs |= tf
                self.write_tabs = "y" if tabs else "n"

## write file
    def put_file(self, fname):
        from os import remove, rename
        tmpfile = fname + ".pyetmp"
        with open(tmpfile, "w") as f:
            for l in self.content:
                if self.write_tabs == 'y':
                    f.write(self.packtabs(l) + '\n')
                else:
                    f.write(l + '\n')
        try:
            remove(fname)
        except:
            pass
        rename(tmpfile, fname)

## expandtabs: hopefully sometimes replaced by the built-in function
def expandtabs(s):
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
        return sb.getvalue(), True
    else:
        return s, False

def pye(*content, tab_size=4, undo=50, device=0):
## prepare content
    gc.collect() ## all (memory) is mine
    slot = [Editor(tab_size, undo)]
    index = 0
    if content:
        for f in content:
            if index:
                slot.append(Editor(tab_size, undo))
            if type(f) == str and f: ## String = non-empty Filename
                try:
                    slot[index].get_file(f)
                except Exception as err:
                    slot[index].message = "{!r}".format(err)
            elif type(f) == list and len(f) > 0 and type(f[0]) == str:
                slot[index].content = f ## non-empty list of strings -> edit
            index += 1
    else:
        slot[0].get_file(".")
        index = 1
## edit
    Editor.init_tty(device)
    while True:
        try:
            index %= len(slot)
            key = slot[index].edit_loop()  ## edit buffer
            if key == KEY_QUIT:
                if len(slot) == 1: ## the last man standing is kept
                    break
                del slot[index]
            elif key == KEY_GET:
                f = slot[index].line_edit("Open file: ", "", "_.-")
                slot.append(Editor(tab_size, undo))
                index = len(slot) - 1
                slot[index].get_file(f)
            elif key == KEY_NEXT:
                index += 1
        except Exception as err:
            slot[index].message = "{!r}".format(err)
## All windows closed, clean up
    Editor.deinit_tty()
    Editor.yank_buffer = []
## close
    return slot[0].content if (slot[0].fname == "") else slot[0].fname

#ifdef LINUX
if __name__ == "__main__":
    if is_linux:
        import stat
        fd_tty = 0
        if len(sys.argv) > 1:
            name = sys.argv[1:]
            pye(*name, undo=500, device=fd_tty)
        else:
            name = ""
            if not is_micropython:
                mode = os.fstat(0).st_mode
                if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
                    name = sys.stdin.readlines()
                    os.close(0) ## close and repopen /dev/tty
                    fd_tty = os.open("/dev/tty", os.O_RDONLY) ## memorized, if new fd
                    for i, l in enumerate(name):  ## strip and convert
                        name[i], tc = expandtabs(l.rstrip('\r\n\t '))
            pye(name, undo=500, device=fd_tty)
    else:
        print ("\nSorry, this OS is not supported (yet)")
#endif
