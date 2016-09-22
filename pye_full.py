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
#ifdef LINUX
if sys.platform in ("linux", "darwin"):
    import os, signal, tty, termios, select
#endif
#ifdef DEFINES
#define KEY_NONE        0
#define KEY_UP          0x0b
#define KEY_DOWN        0x0d
#define KEY_LEFT        0x1f
#define KEY_RIGHT       0x1e
#define KEY_HOME        0x10
#define KEY_END         0x03
#define KEY_PGUP        0xfff1
#define KEY_PGDN        0xfff2
#define KEY_QUIT        0x11
#define KEY_ENTER       0x0a
#define KEY_BACKSPACE   0x08
#define KEY_WRITE       0x13
#define KEY_TAB         0x09
#define KEY_BACKTAB     0x15
#define KEY_FIND        0x06
#define KEY_GOTO        0x07
#define KEY_FIRST       0x14
#define KEY_LAST        0x02
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
#define KEY_GET         0x0f
#define KEY_MARK        0x0c
#define KEY_DELETE      0x7f
#define KEY_NEXT        0x17
#define KEY_MATCH       0xfffd
#define KEY_INDENT      0xfffe
#define KEY_UNDENT      0xffff
#else
KEY_NONE      = 0
KEY_UP        = 0x0b
KEY_DOWN      = 0x0d
KEY_LEFT      = 0x1f
KEY_RIGHT     = 0x1e
KEY_HOME      = 0x10
KEY_END       = 0x03
KEY_PGUP      = 0xfff1
KEY_PGDN      = 0xfff2
KEY_QUIT      = 0x11
KEY_ENTER     = 0x0a
KEY_BACKSPACE = 0x08
KEY_DELETE    = 0x7f
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
KEY_FIRST     = 0x14
KEY_LAST      = 0x02
KEY_REPLC     = 0x12
KEY_TOGGLE    = 0x01
KEY_GET       = 0x0f
KEY_MARK      = 0x0c
KEY_NEXT      = 0x17
KEY_MATCH     = 0xfffd
KEY_INDENT    = 0xfffe
KEY_UNDENT    = 0xffff
#endif

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
    "\x11"   : KEY_QUIT, ## Ctrl-Q
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
    "\x14"   : KEY_FIRST, ## Ctrl-T
    "\x02"   : KEY_LAST,  ## Ctrl-B
    "\x01"   : KEY_TOGGLE, ## Ctrl-A
    "\x17"   : KEY_NEXT, ## Ctrl-W
    "\x0f"   : KEY_GET, ## Ctrl-O
## other keys
    "\x1b[1;5H": KEY_FIRST, ## Ctrl-Home
    "\x1b[1;5F": KEY_LAST, ## Ctrl-End
    "\x1b[3;5~": KEY_YANK, ## Ctrl-Del
#ifdef BRACKET
    "\x0b"   : KEY_MATCH,## Ctrl-K
#endif
#ifdef MOUSE
    "\x1b[M" : KEY_MOUSE,
#endif
    }
## symbols that are shared between instances of Editor
    yank_buffer = []
    find_pattern = ""
    case = "n"
#ifdef REPLACE
    replc_pattern = ""
#endif

    def __init__(self, tab_size, undo_limit):
        self.top_line = self.cur_line = self.row = self.col = self.margin = 0
        self.tab_size = tab_size
        self.changed = ""
        self.message = self.fname = ""
        self.content = [""]
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
        self.undo_zero = 0
        self.autoindent = "y"
        self.mark = None
#ifndef BASIC
        self.write_tabs = "n"
#endif

#ifdef LINUX
    if sys.platform in ("linux", "darwin"):

        def wr(self,s):
            if isinstance(s, str):
                s = bytes(s, "utf-8")
            os.write(1, s)

        def rd_any(self):
            if sys.implementation.name == "cpython":
                return select.select([self.sdev], [], [], 0)[0] != []
            else:
                return False

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
        def init_tty(device, baud):
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
#ifdef PYBOARD
    if sys.platform == "pyboard":
        def wr(self,s):
            ns = 0
            while ns < len(s): # complicated but needed, since USB_VCP.write() has issues
                res = self.serialcomm.write(s[ns:])
                if res != None:
                    ns += res

        def rd_any(self):
            return self.serialcomm.any()

        def rd(self):
            while not self.serialcomm.any():
                pass
            c = self.serialcomm.read(1)
            flag = c[0]
            while (flag & 0xc0) == 0xc0:   ## utf-8 char collection
                c += self.serialcomm.read(1)
                flag <<= 1
            return c.decode("UTF-8")

        @staticmethod
        def init_tty(device, baud):
            import pyb
            Editor.sdev = device
            if Editor.sdev:
                Editor.serialcomm = pyb.UART(device, baud)
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)

        @staticmethod
        def deinit_tty():
            if not Editor.sdev:
                Editor.serialcomm.setinterrupt(3)
#endif
#if defined(WIPY) || defined(ESP8266)
    if sys.platform in ("WiPy", "esp8266"):
        def wr(self, s):
            sys.stdout.write(s)

        def rd_any(self):
            return False

        def rd(self):
            while True:
                try: return sys.stdin.read(1)
                except: return '\x03'

        @staticmethod
        def init_tty(device, baud):
            pass

        @staticmethod
        def deinit_tty():
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

#ifdef MOUSE
    def mouse_reporting(self, onoff):
        self.wr('\x1b[?9h' if onoff else '\x1b[?9l') ## enable/disable mouse reporting
#endif
#ifdef SCROLL
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
        self.wr("\x1bD " * scrolling)
#endif
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
#ifdef SCROLL
        self.scroll_region(Editor.height)
#endif
#ifdef MOUSE
        self.mouse_reporting(True) ## enable mouse reporting
#endif
#ifdef LINUX
        if sys.platform in ("linux", "darwin") and sys.implementation.name == "cpython":
            signal.signal(signal.SIGWINCH, Editor.signal_handler)
#endif
        if sys.implementation.name == "micropython":
            gc.collect()
            if flag: self.message = "{} Bytes Memory available".format(gc.mem_free())

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
#ifdef MOUSE
                else: ## special for mice
                    self.mouse_fct = ord((self.rd())) ## read 3 more chars
                    self.mouse_x = ord(self.rd()) - 33
                    self.mouse_y = ord(self.rd()) - 33
                    if self.mouse_fct == 0x61:
                        return KEY_SCRLDN, ""
                    elif self.mouse_fct == 0x60:
                        return KEY_SCRLUP, ""
                    else:
                        return KEY_MOUSE, "" ## do nothing but set the cursor
#endif
            else:
                return KEY_NONE, in_buffer

    def display_window(self): ## Update window and status line
## Force cur_line and col to be in the reasonable bounds
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
        self.col = max(0, min(self.col, len(self.content[self.cur_line])))
## Check if Column is out of view, and align margin if needed
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
                l = (self.mark != None and (
                    (self.mark <= i <= self.cur_line) or (self.cur_line <= i <= self.mark)),
                     self.content[i][self.margin:self.margin + Editor.width])
                if l != Editor.scrbuf[c]: ## line changed, print it
                    self.goto(c, 0)
                    if l[0]: self.hilite(2)
                    self.wr(l[1])
                    if len(l[1]) < Editor.width:
                        self.clear_to_eol()
                    if l[0]: self.hilite(0)
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
        return (len(line) - len(line.lstrip(" ")) if pos == None else ## at line start
                len(line[:pos]) - len(line[:pos].rstrip(" ")))

    def line_range(self):
        return ((self.mark, self.cur_line + 1) if self.mark < self.cur_line else
                (self.cur_line, self.mark + 1))

    def line_edit(self, prompt, default):  ## better one: added cursor keys and backsp, delete
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
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(0)
                return res
            elif key == KEY_QUIT: ## Abort
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
            elif key == KEY_HOME:
                self.wr("\b" * pos)
                pos = 0
            elif key == KEY_END:
                self.wr(res[pos:])
                pos = len(res)
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
            elif key == KEY_ZAP: ## Get from content
                if Editor.yank_buffer:
                    self.wr('\b' * pos + ' ' * len(res) + '\b' * len(res))
                    res = Editor.yank_buffer[0].strip()[:Editor.width - len(prompt) - 2]
                    self.wr(res)
                    pos = len(res)
            elif key == KEY_NONE: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + char + res[pos:]
                    self.wr(res[pos])
                    pos += len(char)
                    push_msg(res[pos:]) ## update tail

## This is the regex version of find.
    def find_in_file(self, pattern, col, end):
        try: from ure import compile
        except: from re import compile
#define REGEXP 1
        Editor.find_pattern = pattern ## remember it
        if Editor.case != "y":
            pattern = pattern.lower()
        try:
            rex = compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return -1
        scol = col
        for line in range(self.cur_line, end):
            l = self.content[line]
            if Editor.case != "y":
                l = l.lower()
## since micropython does not support span, a step-by_step match has to be performed
            ecol = 1 if pattern[0] == '^' else len(l) + 1
            for i in range(scol, ecol):
                match = rex.match(l[i:])
                if match: ## bingo!
                    self.col = i
                    self.cur_line = line
                    return len(match.group(0))
            scol = 0
        else:
            self.message = pattern + " not found"
            return -1

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

    def handle_edit_keys(self, key, char): ## keys which change content
        l = self.content[self.cur_line]
        if key == KEY_DOWN:
#ifdef SCROLL
            if self.cur_line < self.total_lines - 1:
#endif
                self.cur_line += 1
#ifdef SCROLL
                if self.cur_line == self.top_line + Editor.height:
                    self.scroll_down(1)
#endif
        elif key == KEY_UP:
#ifdef SCROLL
            if self.cur_line > 0:
#endif
                self.cur_line -= 1
#ifdef SCROLL
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
#endif
        elif key == KEY_LEFT:
#ifndef BASIC
            if self.col == 0 and self.cur_line > 0:
                self.cur_line -= 1
                self.col = len(self.content[self.cur_line])
#ifdef SCROLL
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
#endif
            else:
#endif
                self.col -= 1
        elif key == KEY_RIGHT:
#ifndef BASIC
            if self.col >= len(l) and self.cur_line < self.total_lines - 1:
                self.col = 0
                self.cur_line += 1
#ifdef SCROLL
                if self.cur_line == self.top_line + Editor.height:
                    self.scroll_down(1)
#endif
            else:
#endif
                self.col += 1
        elif key == KEY_DELETE:
            if self.mark != None:
                self.delete_lines(False)
            elif self.col < len(l):
                self.undo_add(self.cur_line, [l], KEY_DELETE)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines: ## test for last line
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], KEY_NONE)
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
        elif key == KEY_BACKSPACE:
            if self.mark != None:
                self.delete_lines(False)
            elif self.col > 0:
                self.undo_add(self.cur_line, [l], KEY_BACKSPACE)
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
#ifndef BASIC
            elif self.cur_line > 0: # at the start of a line, but not the first
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], KEY_NONE)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += self.content.pop(self.cur_line)
                self.cur_line -= 1
                self.total_lines -= 1
#endif
        elif key == KEY_NONE: ## character to be added
            self.mark = None
            self.undo_add(self.cur_line, [l], 0x20 if char == " " else 0x41)
            self.content[self.cur_line] = l[:self.col] + char + l[self.col:]
            self.col += len(char)
        elif key == KEY_HOME:
            ni = self.spaces(l)
            self.col = ni if self.col != ni else 0
        elif key == KEY_END:
            self.col = len(l)
        elif key == KEY_PGUP:
            self.cur_line -= Editor.height
        elif key == KEY_PGDN:
            self.cur_line += Editor.height
        elif key == KEY_FIND:
            pat = self.line_edit("Find: ", Editor.find_pattern)
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
#ifndef BASIC
        elif key == KEY_FIRST: ## first line
            self.cur_line = 0
        elif key == KEY_LAST: ## last line
            self.cur_line = self.total_lines - 1
            self.row = Editor.height - 1 ## will be fixed if required
#endif
        elif key == KEY_TOGGLE: ## Toggle Autoindent/Statusline/Search case
            pat = self.line_edit("Case Sensitive Search {}, Autoindent {}"
#ifndef BASIC
            ", Tab Size {}, Write Tabs {}"
#endif
            ": ".format(Editor.case, self.autoindent
#ifndef BASIC
            , self.tab_size, self.write_tabs
#endif
            ), "")
            try:
                res =  [i.strip().lower() for i in pat.split(",")]
                if res[0]: Editor.case       = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: self.autoindent = 'y' if res[1][0] == 'y' else 'n'
#ifndef BASIC
                if res[2]: self.tab_size = int(res[2])
                if res[3]: self.write_tabs = 'y' if res[3][0] == 'y' else 'n'
#endif
            except:
                pass
#ifdef MOUSE
        elif key == KEY_MOUSE: ## Set Cursor
            if self.mouse_y < Editor.height:
                self.col = self.mouse_x + self.margin
                self.cur_line = self.mouse_y + self.top_line
                if self.mouse_fct in (0x22, 0x30): ## Right/Ctrl button on Mouse
                    self.mark = self.cur_line if self.mark == None else None
        elif key == KEY_SCRLUP: ##
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + Editor.height - 1)
#ifdef SCROLL
                self.scroll_up(3)
#endif
        elif key == KEY_SCRLDN: ##
            if self.top_line + Editor.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
#ifdef SCROLL
                self.scroll_down(3)
#endif
#endif
#ifdef BRACKET
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
#endif
        elif key == KEY_MARK:
            self.mark = self.cur_line if self.mark == None else None
        elif key == KEY_ENTER:
            self.mark = None
            self.undo_add(self.cur_line, [l], KEY_NONE, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if self.autoindent == "y": ## Autoindent
                ni = min(self.spaces(l), self.col)  ## query indentation
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == KEY_TAB:
#ifdef INDENT
            if self.mark == None:
#endif
                ni = self.tab_size - self.col % self.tab_size ## determine spaces to add
                self.undo_add(self.cur_line, [l], KEY_TAB)
                self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
                self.col += ni
#ifdef INDENT
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_INDENT, lrange[1] - lrange[0]) ## undo replaces
                for i in range(lrange[0],lrange[1]):
                    if len(self.content[i]) > 0:
                        self.content[i] = ' ' * (self.tab_size - self.spaces(self.content[i]) % self.tab_size) + self.content[i]
#endif
        elif key == KEY_BACKTAB:
#ifdef INDENT
            if self.mark == None:
#endif
                ni = min((self.col - 1) % self.tab_size + 1, self.spaces(l, self.col)) ## determine spaces to drop
                if ni > 0:
                    self.undo_add(self.cur_line, [l], KEY_BACKTAB)
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
#ifdef INDENT
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_UNDENT, lrange[1] - lrange[0]) ## undo replaces
                for i in range(lrange[0],lrange[1]):
                    ns = self.spaces(self.content[i])
                    if ns > 0:
                        self.content[i] = self.content[i][(ns - 1) % self.tab_size + 1:]
#endif
#ifdef REPLACE
        elif key == KEY_REPLC:
            count = 0
            pat = self.line_edit("Replace: ", Editor.find_pattern)
            if pat:
                rpat = self.line_edit("With: ", Editor.replc_pattern)
                if rpat != None: ## start with setting up loop parameters
                    Editor.replc_pattern = rpat
                    q = ''
                    cur_line = self.cur_line ## remember line
                    if self.mark != None: ## Replace in Marked area
                        (self.cur_line, end_line) = self.line_range()
                        self.col = 0
                    else: ## replace from cur_line to end
                        end_line = self.total_lines
                    self.message = "Replace (yes/No/all/quit) ? "
                    while True: ## and go
                        ni = self.find_in_file(pat, self.col, end_line)
                        if ni >= 0: ## Pattern found
                            if q != 'a':
                                self.display_window()
                                key, char = self.get_input()  ## Get Char of Fct.
                                q = char.lower()
                            if q == 'q' or key == KEY_QUIT:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], KEY_NONE)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                            else: ## everything else is no
                                 self.col += 1
#ifdef REGEXP
                            if self.col >= len(self.content[self.cur_line]): ## catch the case of replacing line ends
                                self.cur_line += 1
                                self.col = 0
#endif
                        else: ## not found, quit
                            break
                    self.cur_line = cur_line ## restore cur_line
                    self.message = "'{}' replaced {} times".format(pat, count)
#endif
        elif key == KEY_YANK:  # delete line or line(s) into buffer
            if self.mark != None: self.delete_lines(True)
        elif key == KEY_DUP:  # copy line(s) into buffer
            if self.mark != None:
                lrange = self.line_range()
                Editor.yank_buffer = self.content[lrange[0]:lrange[1]]
                self.mark = None
        elif key == KEY_ZAP: ## insert buffer
            if Editor.yank_buffer:
                if self.mark != None: self.delete_lines(False)
                self.undo_add(self.cur_line, None, KEY_NONE, -len(Editor.yank_buffer))
                self.content[self.cur_line:self.cur_line] = Editor.yank_buffer # insert lines
                self.total_lines += len(Editor.yank_buffer)
        elif key == KEY_WRITE:
            fname = self.line_edit("Save File: ", self.fname)
            if fname:
                self.put_file(fname)
                self.changed = '' ## clear change flag
                self.undo_zero = len(self.undo) ## remember state
                if not self.fname: self.fname = fname ## remember (new) name
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
                if len(self.undo) == self.undo_zero: self.changed = ''
                self.mark = None
        elif key == KEY_REDRAW:
            self.redraw(True)

    def edit_loop(self): ## main editing loop
        if not self.content: ## ensure content
            self.content = [""]
        self.total_lines = len(self.content)
        self.redraw(self.message == "")

        while True:
            if not self.rd_any(): ## skip update if a char is waiting
                self.display_window()  ## Update & display window
            key, char = self.get_input()  ## Get Char of Fct-key code
            self.message = '' ## clear message

            if key == KEY_QUIT:
                if self.changed:
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
#ifdef SCROLL
                self.scroll_region(0)
#endif
#ifdef MOUSE
                self.mouse_reporting(False) ## disable mouse reporting
#endif
                self.goto(Editor.height, 0)
                self.clear_to_eol()
                self.undo = []
                return key
            elif key in (KEY_NEXT, KEY_GET):
                return key
            else:
                self.handle_edit_keys(key, char)

## packtabs: replace sequence of space by tab
#ifndef BASIC
    def packtabs(self, s):

        try: from uio import StringIO
        except: from _io import StringIO

        sb = StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if (len(c) - len(cr)) > 1:
                sb.write(cr + "\t") ## Spaces at the end of a section
            else: sb.write(c)
        return sb.getvalue()
#endif
## Read file into content
    def get_file(self, fname):
        from os import listdir
        try:    from uos import stat
        except: from os import stat
        if not fname:
            fname = self.line_edit("Open file: ", "")
        if fname:
            self.fname = fname
            if fname in ('.', '..') or (stat(fname)[0] & 0x4000): ## Dir
                self.content = ["Directory '{}'".format(fname), ""] + sorted(listdir(fname))
            else:
                if True:
#ifdef LINUX
                    pass
                if sys.implementation.name == "cpython":
                    with open(fname, errors="ignore") as f:
                        self.content = f.readlines()
                else:
#endif
                    with open(fname) as f:
                        self.content = f.readlines()
#ifndef BASIC
                Editor.tab_seen = 'n'
#endif
                for i in range(len(self.content)):  ## strip and convert
                    self.content[i] = expandtabs(self.content[i].rstrip('\r\n\t '))
#ifndef BASIC
                self.write_tabs = Editor.tab_seen
#endif

## write file
    def put_file(self, fname):
        if True:
#ifdef LINUX
            pass
        if sys.platform in ("linux", "darwin"):
            from os import unlink, rename
            remove = unlink
        else:
#endif
            from uos import remove, rename
        tmpfile = fname + ".pyetmp"
        with open(tmpfile, "w") as f:
            for l in self.content:
#ifndef BASIC
                if self.write_tabs == 'y':
                    f.write(self.packtabs(l) + '\n')
                else:
#endif
                    f.write(l + '\n')
        try:    remove(fname)
        except: pass
        rename(tmpfile, fname)

## expandtabs: hopefully sometimes replaced by the built-in function
def expandtabs(s):
    try: from uio import StringIO
    except: from _io import StringIO

    if '\t' in s:
#ifndef BASIC
        Editor.tab_seen = 'y'
#endif
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

def pye(*content, tab_size = 4, undo = 50, device = 0, baud = 115200):
## prepare content
    gc.collect() ## all (memory) is mine
    slot = [Editor(tab_size, undo)]
    index = 0
    if content:
        for f in content:
            if index: slot.append(Editor(tab_size, undo))
            if type(f) == str and f: ## String = non-empty Filename
                try: slot[index].get_file(f)
                except: slot[index].message = "File not found"
            elif type(f) == list and len(f) > 0 and type(f[0]) == str:
                slot[index].content = f ## non-empty list of strings -> edit
            index += 1
## edit
    Editor.init_tty(device, baud)
    while True:
        try:
            index %= len(slot)
            key = slot[index].edit_loop()  ## edit buffer
            if key == KEY_QUIT:
                if len(slot) == 1: ## the last man standing is kept
                    break
                del slot[index]
            elif key == KEY_GET:
                slot.append(Editor(tab_size, undo))
                index = len(slot) - 1
                slot[index].get_file(None)
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
    if sys.platform in ("linux", "darwin"):
        import stat
        fd_tty = 0
        if len(sys.argv) > 1:
            name = sys.argv[1:]
            pye(*name, undo = 500, device=fd_tty)
        else:
            name = ""
            if sys.implementation.name == "cpython":
                mode = os.fstat(0).st_mode
                if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
                    name = sys.stdin.readlines()
                    os.close(0) ## close and repopen /dev/tty
                    fd_tty = os.open("/dev/tty", os.O_RDONLY) ## memorized, if new fd
                    for i in range(len(name)):  ## strip and convert
                        name[i] = expandtabs(name[i].rstrip('\r\n\t '))
            pye(name, undo = 500, device=fd_tty)
    else:
        print ("\nSorry, this OS is not supported (yet)")
#endif
