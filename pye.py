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
## - Goto Line, Yank (delete line into buffer), Zap (insert buffer)
## - moved main into a function with some optional parameters
## - Added a status line, line number column and single line prompts for Quit, Save, Find and Goto
## - Added mouse support for pointing and scrolling
##
import sys
import gc
import _io
##
#ifdef LINUX
if sys.platform in ("linux", "darwin"):
    import os
#endif
#ifdef PYBOARD
if sys.platform == "pyboard":
    import pyb
#endif
#ifdef DEFINES
#define KEY_UP          0x1a
#define KEY_DOWN        0x0b
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
#else
KEY_UP        = 0x1a
KEY_DOWN      = 0x0b
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
KEY_FIND      = 0x06
KEY_GOTO      = 0x07
KEY_MOUSE     = 0x1b
KEY_SCRLUP    = 0x1c
KEY_SCRLDN    = 0x1d
KEY_FIND_AGAIN= 0x0e
KEY_REDRAW    = 0x05
#ifndef BASIC
KEY_FIRST     = 0x02
KEY_LAST      = 0x14
KEY_BACKTAB   = 0x15
KEY_YANK      = 0x18
KEY_ZAP       = 0x16
KEY_TOGGLE    = 0x01
KEY_REPLC     = 0x12
KEY_DUP       = 0x04
#endif
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
    b"\x03"   : KEY_QUIT, ## Ctrl-C as well
    b"\r"     : KEY_ENTER,
    b"\n"     : KEY_ENTER,
    b"\x7f"   : KEY_BACKSPACE, ## Ctrl-? (127)
    b"\x08"   : KEY_BACKSPACE,
    b"\x1b[3~": KEY_DELETE,
    b"\x13"   : KEY_WRITE,  ## Ctrl-S
    b"\x06"   : KEY_FIND, ## Ctrl-F
    b"\x0e"   : KEY_FIND_AGAIN, ## Ctrl-N
    b"\x07"   : KEY_GOTO, ##  Ctrl-G
    b"\x1b[M" : KEY_MOUSE,
    b"\x05"   : KEY_REDRAW, ## Ctrl-E
    b"\x09"   : KEY_TAB,
#ifndef BASIC
    b"\x01"   : KEY_TOGGLE, ## Ctrl-A
    b"\x14"   : KEY_FIRST, ## Ctrl-T
    b"\x1b[1;5H": KEY_FIRST,
    b"\x02"   : KEY_LAST,  ## Ctrl-B
    b"\x1b[1;5F": KEY_LAST,
    b"\x1b[Z" : KEY_BACKTAB, ## Shift Tab
    b"\x15"   : KEY_BACKTAB, ## Ctrl-U
    b"\x1b[3;5~": KEY_YANK,
    b"\x18"   : KEY_YANK, ## Ctrl-X
    b"\x16"   : KEY_ZAP, ## Ctrl-V
    b"\x12"   : KEY_REPLC, ## Ctrl-R
    b"\x04"   : KEY_DUP, ## Ctrl-D
#endif
    }

    def __init__(self, tab_size):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.col_width = 0
        self.col_spc = ''
        self.margin = 0
        self.scrolling = 0
        self.tab_size = tab_size
        self.changed = ' '
        self.message = ""
        self.find_pattern = ""
        self.replc_pattern = ""
        self.y_buffer = []
        self.content = [""]
        self.fname = None
        self.lastkey = 0
        self.autoindent = "y"
        self.case = "n"
#ifdef LINUX
    if sys.platform in ("linux", "darwin"):

        @staticmethod
        def wr(s):
            if isinstance(s, str):
                s = bytes(s, "utf-8")
            os.write(1, s)

        @staticmethod
        def rd():
           return os.read(Editor.sdev,1)
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
        elif mode == 2:
            Editor.wr(b"\x1b[2;7m")
        else:
            Editor.wr(b"\x1b[0m")

    @staticmethod
    def get_screen_size():
    ## Set cursor far off and ask for reporting its position = size of the window.
        Editor.wr('\x1b[999;999H\x1b[6n')
        pos = b''
        char = Editor.rd() ## expect ESC[yyy;xxxR
        while char != b'R':
            pos += char
            char = Editor.rd()
        (height, width) = [int(i, 10) for i in pos[2:].split(b';')]
        return (height-1, width)

    @staticmethod
    def mouse_reporting(onoff):
        if onoff:
            Editor.wr('\x1b[?9h') ## enable mouse reporting
        else:
            Editor.wr('\x1b[?9l') ## enable mouse reporting

    @staticmethod
    def scroll_region(stop):
        if stop:
            Editor.wr('\x1b[1;%dr' % stop) ## enable partial scrolling
        else:
            Editor.wr('\x1b[r') ## enable partial scrolling
#ifndef BASIC
    @staticmethod
    def scroll_lines(updown, lines):
        if updown:
            Editor.wr("\x1bM" * lines) ## Scroll up
        else:
            Editor.wr("\x1bD " * lines) ## Scroll down
#endif
    def set_screen_parms(self, lines, lnum):
        (self.height, self.width) = self.get_screen_size()
        self.scroll_region(self.height)
        self.scrbuf = ["\x04"] * self.height ## force delete
        if lnum: ## prepare for line number column
            lnum = 3
            if self.total_lines > 900:  lnum = 4
            if self.total_lines > 9000: lnum = 5
            self.col_width = lnum + 1 ## width of line no. col
            self.col_fmt = "%%%dd " % lnum
            self.col_spc = " " * self.col_width
            self.width -= self.col_width

    @staticmethod
    def print_no(row, lnum):
        Editor.goto(row, 0)
        if lnum:
            Editor.hilite(2)
            Editor.wr(lnum)
            Editor.hilite(0)

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
                if c == KEY_MOUSE: ## special for mice
                    mf = ord((Editor.rd())) & 0xe3 ## read 3 more chars
                    self.mouse_x = ord(Editor.rd()) - 33
                    self.mouse_y = ord(Editor.rd()) - 33
                    if mf == 0x61:
                        return KEY_SCRLDN
                    elif mf == 0x60:
                        return KEY_SCRLUP
                    else:
                        return KEY_MOUSE ## do nothing but set the cursor
                else:
                    return c
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
#ifndef BASIC
        if self.scrolling < 0:  ## scroll down by n lines
            self.scrbuf[-self.scrolling:] = self.scrbuf[:self.scrolling]
            self.scrbuf[:-self.scrolling] = [''] * -self.scrolling
            self.goto(0, 0)
            self.scroll_lines(True, -self.scrolling)
        elif self.scrolling  > 0:  ## scroll up by n lines
            self.scrbuf[:-self.scrolling] = self.scrbuf[self.scrolling:]
            self.scrbuf[-self.scrolling:] = [''] * self.scrolling
            self.goto(self.height - 1, 0)
            self.scroll_lines(False, self.scrolling)
        self.scrolling = 0
#endif
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: ## at empty bottom screen part
                if self.scrbuf[c] != '':
                    self.print_no(c, self.col_spc)
                    self.clear_to_eol()
                    self.scrbuf[c] = ''
            else:
                l = self.content[i][self.margin:self.margin + self.width]
                if self.col_width > 1:
                    lnum = self.col_fmt % (i + 1)
                else:
                    lnum = ''
                if (lnum + l) != self.scrbuf[c]: ## line changed, print it
                    self.print_no(c, lnum) ## print line no
                    self.wr(l)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = lnum + l
                i += 1
## display Status-Line
        if self.status == "y" or self.message:
            self.goto(self.height, 0)
            self.clear_to_eol() ## moved up for mate/xfce4-terminal issue with scroll region
            self.hilite(1)
            if self.col_width > 0:
                self.wr(self.col_fmt % self.total_lines)
            self.wr("%c Ln: %d Col: %d  %s" % (self.changed, self.cur_line + 1, self.col + 1, self.message))
            self.hilite(0)
        self.cursor(True)
        self.goto(self.row, self.col - self.margin + self.col_width)

    def clear_status(self):
        if (self.status != "y") and self.message:
            self.goto(self.height, 0)
            self.clear_to_eol()
        self.message = ''

    @staticmethod
    def spaces(line, pos = 0): ## count spaces
        if pos: ## left to the cursor
            return len(line[:pos]) - len(line[:pos].rstrip(" "))
        else: ## at line start
            return len(line) - len(line.lstrip(" "))

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
                if len(prompt) + len(res) < self.width - 1:
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
            self.message = pattern + " not found"
            return 0
        self.col = match + spos
        self.cur_line = line
        self.message = ' ' ## force status once
        return len(pattern)

    def handle_cursor_keys(self, key): ## keys which move, sanity checks later
        if key == KEY_DOWN:
            if self.cur_line < self.total_lines - 1:
                self.cur_line += 1
                if self.cur_line == self.top_line + self.height: self.scrolling = 1
        elif key == KEY_UP:
            if self.cur_line > 0:
                if self.cur_line == self.top_line: self.scrolling = -1
                self.cur_line -= 1
        elif key == KEY_LEFT:
            self.col -= 1
        elif key == KEY_RIGHT:
            self.col += 1
        elif key == KEY_HOME:
            ns = self.spaces(self.content[self.cur_line])
            if self.col > ns:
                self.col = ns
            else:
                self.col = 0
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
                self.row = self.row = self.height >> 1
        elif key == KEY_GOTO: ## goto line
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = self.height >> 1
                except:
                    pass
        elif key == KEY_MOUSE: ## Set Cursor
            if self.mouse_y < self.height:
                self.col = self.mouse_x + self.margin - self.col_width
                self.cur_line = self.mouse_y + self.top_line
            self.message = ' '
        elif key == KEY_SCRLUP: ##
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + self.height - 1)
                self.scrolling = -3
        elif key == KEY_SCRLDN: ##
            if self.top_line + self.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scrolling = 3
#ifndef BASIC
        elif key == KEY_TOGGLE: ## Toggle Autoindent/Statusline/Search case
            pat = self.line_edit("Case Sensitive Search %c, Statusline %c, Autoindent %c: " % (self.case, self.status, self.autoindent), "")
            try:
                res =  [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case = res[0][0]
                if res[1]: self.status = res[1][0]
                if res[2]: self.autoindent = res[2][0]
            except:
                pass
        elif key == KEY_FIRST: ## first line
            self.cur_line = 0
        elif key == KEY_LAST: ## last line
            self.cur_line = self.total_lines - 1
            self.row = self.height - 1
            self.message = ' ' ## force status once
#endif
        else:
            return False
        return True

    def handle_edit_key(self, key): ## keys which change content
        l = self.content[self.cur_line]
        if key == KEY_ENTER:
            self.content[self.cur_line] = l[:self.col]
            ni = 0
#ifndef BASIC
            if self.autoindent == "y": ## Autoindent
                ni = min(self.spaces(l, 0), self.col)  ## query indentation
                r = self.content[self.cur_line].partition("\x23")[0].rstrip() ## \x23 == #
                if r and r[-1] == ':' and self.col >= len(r): ## look for : as the last non-space before comment
                    ni += self.tab_size
#endif
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
            self.changed = '*'
        elif key == KEY_BACKSPACE:
            if self.col > 0:
                ni = 1
#ifndef BASIC
                if self.autoindent == "y" and self.spaces(l, 0) == self.col: ## Autoindent, Backspace does Backtab
                    ni = (self.col - 1) % self.tab_size + 1
#endif
                self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                self.col -= ni
                self.changed = '*'
#ifndef BASIC
            elif self.cur_line: # at the start of a line, but not the first
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += l
                del self.content[self.cur_line]
                self.cur_line -= 1
                self.total_lines -= 1
                self.changed = '*'
#endif
        elif key == KEY_DELETE:
            if self.col < len(l):
                l = l[:self.col] + l[self.col + 1:]
                self.content[self.cur_line] = l
                self.changed = '*'
            elif (self.cur_line + 1) < self.total_lines: ## test for last line
                ni = 0
#ifndef BASIC
                if self.autoindent == "y": ## Autoindent reversed
                    ni = self.spaces(self.content[self.cur_line + 1])
#endif
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)[ni:]
                self.total_lines -= 1
                self.changed = '*'
#ifndef BASIC
        elif key == KEY_TAB: ## TABify line
            ns = self.spaces(l, 0)
            if ns and self.col < ns: # at BOL
                ni = self.tab_size - ns % self.tab_size
            else:
                ni = self.tab_size - self.col % self.tab_size
            self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
            if ns == len(l) or self.col >= ns: # lines of spaces or in text
                self.col += ni # move cursor
            self.changed = '*'
        elif key == KEY_BACKTAB: ## unTABify line
            ns = self.spaces(l, 0)
            if ns and self.col < ns: # at BOL
                ni = (ns - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[ni:]
                self.changed = '*'
            else: # left to cursor & move
                ns = self.spaces(l, self.col)
                ni = (self.col - 1) % self.tab_size + 1
                if (ns >= ni):
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
                    self.changed = '*'
        elif key == KEY_YANK:  # delete line into buffer
            if key == self.lastkey: # yank series?
                self.y_buffer.append(l) # add line
            else:
                del self.y_buffer # set line
                self.y_buffer = [l]
            if self.total_lines > 1: ## not a single line
                del self.content[self.cur_line]
                self.total_lines -= 1
                if self.cur_line  >= self.total_lines: ## on last line move pointer
                    self.cur_line -= 1
            else: ## line is kept but wiped
                self.content[self.cur_line] = ''
            self.changed = '*'
        elif key == KEY_DUP:  # copy line into buffer and go down one line
            if key == self.lastkey: # dup series?
                self.y_buffer.append(l) # add line
            else:
                del self.y_buffer # set line
                self.y_buffer = [l]
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
        elif key == KEY_ZAP: ## insert buffer
            if self.y_buffer:
                self.content[self.cur_line:self.cur_line] = self.y_buffer # insert lines
                self.total_lines += len(self.y_buffer)
                self.changed = '*'
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
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                                self.changed = '*'
                            else: ## everything else is no
                                self.col += 1
                        else:
                            break
                    self.message = "'%s' replaced %d times" % (pat, count)
#endif
        elif key == KEY_WRITE:
            fname = self.fname
            if fname == None:
                fname = ""
            fname = self.line_edit("File Name: ", fname)
            if fname:
                try:
                    with open(fname, "w") as f:
                        for l in self.content:
                            f.write(l + '\n')
                    self.changed = " "
                    self.fname = fname
                except:
                    pass
        elif key >= 0x20: ## character to be added
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
            self.changed = '*'

    def edit_loop(self, lnum): ## main editing loop
        self.total_lines = len(self.content)
        ## strip trailing whitespace and expand tabs
        for i in range(self.total_lines):
            self.content[i] = self.expandtabs(self.content[i].rstrip('\r\n\t '))
        self.set_screen_parms(self.total_lines, lnum)

        while True:
            self.display_window()  ## Update & display window
            key = self.get_input()  ## Get Char of Fct-key code
            self.clear_status() ## From messages

            if key == KEY_QUIT:
                if self.changed != ' ' and self.fname != None:
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                return None
            elif key == KEY_REDRAW:
                del self.scrbuf
                self.set_screen_parms(self.total_lines, lnum)
                self.row = min(self.height - 1, self.row)
            elif  self.handle_cursor_keys(key):
                pass
            else: self.handle_edit_key(key)
            self.lastkey = key

    def init_tty(self, device, baud, fd_tty):
#ifdef PYBOARD
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
                self.status = "n"

            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
                self.status = "y"
            Editor.sdev = device
#endif
#ifdef LINUX
        if sys.platform in ("linux", "darwin"):
            import tty, termios
            self.org_termios = termios.tcgetattr(fd_tty)
            tty.setraw(fd_tty)
            Editor.sdev = fd_tty
            self.status = "y"
#endif
        self.mouse_reporting(True) ## disable mouse reporting, enable scrolling

    def deinit_tty(self):
        ## Do not leave cursor in the middle of screen
        self.mouse_reporting(False) ## disable mouse reporting, enable scrolling
        self.scroll_region(0)
        self.goto(self.height, 0)
        self.clear_to_eol()
#ifdef PYBOARD
        if sys.platform == "pyboard" and not Editor.sdev:
            Editor.serialcomm.setinterrupt(3)
#endif
#ifdef LINUX
        if sys.platform in ("linux", "darwin"):
            import termios
            termios.tcsetattr(Editor.sdev, termios.TCSANOW, self.org_termios)
#endif
## expandtabs: hopefully sometimes replaced by the built-in function
    @staticmethod
    def expandtabs(s):
        if '\t' in s:
            sb = _io.StringIO()
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

def pye(content = None, tab_size = 4, lnum = 4, device = 0, baud = 115200, fd_tty = 0):
## prepare content
    e = Editor(tab_size)
    if type(content) == str: ## String = Filename
        e.fname = content
        if e.fname:  ## non-empty String -> read it
            try:
#ifdef LINUX
                if sys.implementation.name == "cpython":
                    with open(e.fname, errors="ignore") as f:
                        e.content = f.readlines()
                else:
#endif
                    with open(e.fname) as f:
                        e.content = f.readlines()
            except Exception as err:
                print ('Could not load %s, Reason: "%s"' % (e.fname, err))
                del e
                return
            else:
                if not e.content: ## empty file
                    e.content = [""]
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        ## non-empty list of strings -> edit
        e.content = content
        if fd_tty: e.fname = ""
## edit
    e.init_tty(device, baud, fd_tty)
    e.edit_loop(lnum)
    e.deinit_tty()
## clean-up
    if e.fname == None:
        content = e.content
    else:
        content = e.fname
    del e
    gc.collect()
    return content

#ifdef LINUX
if __name__ == "__main__":
    if sys.platform in ("linux", "darwin"):
        import getopt
        import os, stat
        args_dict = {'-t' : '4', '-l' : "None", '-h' : "None"}
        usage = ("Usage: python3 pye.py [-t tabsize] [-l] [filename]\n"
                 "Flags: -t x set tabsize\n"
                 "       -l   suppress line number column")
        fd_tty = 0
        try:
            options, args = getopt.getopt(sys.argv[1:],"t:lh") ## get the options -t x -l -h
        except:
            print ("Undefined option in: " + ' '.join(sys.argv[1:]))
            print (usage)
            sys.exit()
        args_dict.update( options ) ## Sort the input into the default parameters
        if args_dict["-h"] != "None":
            print(usage)
            sys.exit()
        if len(args) > 0:
            name = args[0]
        else:
            name = ""
            if sys.implementation.name == "cpython":
                mode = os.fstat(0).st_mode
                if stat.S_ISFIFO(mode) or stat.S_ISREG(mode):
                     name = sys.stdin.readlines()
                     fd_tty = os.open("/dev/tty", os.O_RDONLY) ## tty gets another fd
                     os.close(0) ## now we can close 0
        try:
            tsize = int(args_dict["-t"])
        except:
            tsize = 4
        if args_dict["-l"] != "None":
            lnum = 0
        else:
            lnum = 5
        pye(name, tsize, lnum, fd_tty=fd_tty)
#endif
