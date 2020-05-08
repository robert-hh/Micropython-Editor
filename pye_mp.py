# Origin: robert-hh/Micropython-editor
# Updates by KMatocha ksmatocha@gmail.com
# Added external display output 5/3/2020
# Added UART capability 5/4/2020
# Updated SPI display pinouts 5/5/2020
# Improved scrolling performance by turning display.auto_refresh=False when writing a large amout of changes
#   should probably change this to permanent auto_refresh=False and only update when necessary
# Repaired status line writing 5/5/2020
# Moved some functions to root (init_tty and init_display) to support multiple windows, but single display
#
# ToDo: add highlight function for external display.


import sys, gc
import board, busio # for uart and SPI display 
if sys.platform in ("linux", "darwin"):
    import os, signal, tty, termios
    is_linux = True
else:
    import os
    is_linux = False
if sys.implementation.name == "micropython":
    is_micropython = True
    from uio import StringIO
elif sys.implementation.name == "circuitpython":
    is_micropython = True
    from io import StringIO
else:
    is_micropython = False
    const = lambda x:x
    from _io import StringIO
from re import compile as re_compile
PYE_VERSION = " V2.46x "
KEY_NONE = const(0x00)
KEY_UP = const(0x0b)
KEY_DOWN = const(0x0d)
KEY_LEFT = const(0x1f)
KEY_RIGHT = const(0x1e)
KEY_HOME = const(0x10)
KEY_END = const(0x03)
KEY_PGUP = const(0xfff1)
KEY_PGDN = const(0xfff2)
KEY_WORD_LEFT = const(0xfff3)
KEY_WORD_RIGHT= const(0xfff4)
KEY_SHIFT_UP = const(0xfff5)
KEY_ALT_UP = const(0xffea)
KEY_SHIFT_DOWN= const(0xfff6)
KEY_ALT_DOWN = const(0xffeb)
KEY_SHIFT_LEFT= const(0xfff0)
KEY_SHIFT_RIGHT= const(0xffef)
KEY_SHIFT_CTRL_LEFT= const(0xffed)
KEY_SHIFT_CTRL_RIGHT= const(0xffec)
KEY_QUIT = const(0x11)
KEY_ENTER = const(0x0a)
KEY_BACKSPACE = const(0x08)
KEY_DELETE = const(0x7f)
KEY_DEL_WORD = const(0xfff7)
KEY_WRITE = const(0x13)
KEY_TAB = const(0x09)
KEY_BACKTAB = const(0x15)
KEY_FIND = const(0x06)
KEY_GOTO = const(0x07)
KEY_MOUSE = const(0x1b)
KEY_SCRLUP = const(0x1c)
KEY_SCRLDN = const(0x1d)
KEY_FIND_AGAIN= const(0x0e)
KEY_REDRAW = const(0x05)
KEY_UNDO = const(0x1a)
KEY_REDO = const(0xffee)
KEY_CUT = const(0x18)
KEY_PASTE = const(0x16)
KEY_COPY = const(0x04)
KEY_FIRST = const(0x14)
KEY_LAST = const(0x02)
KEY_REPLC = const(0x12)
KEY_TOGGLE = const(0x01)
KEY_GET = const(0x0f)
KEY_MARK = const(0x0c)
KEY_NEXT = const(0x17)
KEY_COMMENT = const(0xfffc)
KEY_MATCH = const(0xfffd)
KEY_INDENT = const(0xfffe)
KEY_DEDENT = const(0xffff)
class Editor:
    KEYMAP = {
    "\x1b[A" : KEY_UP,
    "\x1b[1;2A": KEY_SHIFT_UP,
    "\x1b[1;3A": KEY_ALT_UP,
    "\x1b[B" : KEY_DOWN,
    "\x1b[1;2B": KEY_SHIFT_DOWN,
    "\x1b[1;3B": KEY_ALT_DOWN,
    "\x1b[D" : KEY_LEFT,
    "\x1b[1;2D": KEY_SHIFT_LEFT,
    "\x1b[1;6D": KEY_SHIFT_CTRL_LEFT,
    "\x1b[C" : KEY_RIGHT,
    "\x1b[1;2C": KEY_SHIFT_RIGHT,
    "\x1b[1;6C": KEY_SHIFT_CTRL_RIGHT,
    "\x1b[H" : KEY_HOME,
    "\x1bOH" : KEY_HOME,
    "\x1b[1~": KEY_HOME,
    "\x1b[F" : KEY_END,
    "\x1bOF" : KEY_END,
    "\x1b[4~": KEY_END,
    "\x1b[5~": KEY_PGUP,
    "\x1b[6~": KEY_PGDN,
    "\x1b[1;5D": KEY_WORD_LEFT,
    "\x1b[1;5C": KEY_WORD_RIGHT,
    "\x03" : KEY_COPY,
    "\r" : KEY_ENTER,
    "\x7f" : KEY_BACKSPACE,
    "\x1b[3~": KEY_DELETE,
    "\x1b[Z" : KEY_BACKTAB,
    "\x19" : KEY_REDO,
#    "\x08" : KEY_REPLC,
    "\x08" : KEY_BACKSPACE,
    "\x12" : KEY_REPLC,
    "\x11" : KEY_QUIT,
    "\n" : KEY_ENTER,
    "\x13" : KEY_WRITE,
    "\x06" : KEY_FIND,
    "\x0e" : KEY_FIND_AGAIN,
    "\x07" : KEY_GOTO,
    "\x05" : KEY_REDRAW,
    "\x1a" : KEY_UNDO,
    "\x09" : KEY_TAB,
    "\x15" : KEY_BACKTAB,
    "\x18" : KEY_CUT,
    "\x16" : KEY_PASTE,
    "\x04" : KEY_COPY,
    "\x0c" : KEY_MARK,
    "\x00" : KEY_MARK,
    "\x14" : KEY_FIRST,
    "\x02" : KEY_LAST,
    "\x01" : KEY_TOGGLE,
    "\x17" : KEY_NEXT,
    "\x0f" : KEY_GET,
    "\x10" : KEY_COMMENT,
    "\x1b[1;5A": KEY_SCRLUP,
    "\x1b[1;5B": KEY_SCRLDN,
    "\x1b[1;5H": KEY_FIRST,
    "\x1b[1;5F": KEY_LAST,
    "\x1b[3;5~": KEY_DEL_WORD,
    "\x0b" : KEY_MATCH,
    "\x1b[M" : KEY_MOUSE,
    }
    yank_buffer = []
    find_pattern = ""
    case = "n"
    autoindent = "y"
    replc_pattern = ""
    comment_char = "\x23 "
    word_char = "_\\"
    uart=''
    display=''


    inputUART= True # set True if using uart as input, set False if using stdin (serial bus)
    displayOutput=True # displayOutput=True means to use connected display, False outputs on stdout
    displayYPixels=240 # dimensions of the display
    displayXPixels=240 # display dimensions

    def __init__(self, tab_size, undo_limit):
        self.top_line = self.cur_line = self.row = self.vcol = self.col = self.margin = 0
        self.tab_size = tab_size
        self.changed = ''
        self.hash = 0
        self.message = self.fname = ""
        self.content = [""]
        self.undo = []
        self.undo_limit = undo_limit
        self.redo = []
        self.mark = None
        self.write_tabs = "n"
        self.work_dir = os.getcwd()
        self.g='' # group to hold the terminal displays

        self.init_terminal() # create the display terminal, if required.

    if is_micropython and not is_linux:
        def wr(self, s):
            if Editor.displayOutput:
                self.mainTerminal.write(s) ## writes to terminalio
            else:
                sys.stdout.write(s)

        def rd(self):
            if Editor.inputUART:
                while True:
                    myInput=Editor.uart.read(1)# for using uart
                    if myInput==None:
                        pass
                    else:

                        return myInput.decode('utf-8')  # use this if UART is sending int  before 5/4/2020

            else:
                myInput=sys.stdin.read(1)

                return myInput




        def rd_raw(self): 
            return Editor.rd_raw_fct(1)

        def init_terminal(self):
            if Editor.displayOutput:

                from simpleTerminal import simpleTerminal # https://github.com/kmatch98/simpleTerminal
                import terminalio, displayio
                myFont=terminalio.FONT # default font

                # instance the main text terminal
                from math import floor
                fontW, fontH = myFont.get_bounding_box()
                numRows=floor(Editor.displayYPixels/fontH)-1 # subtract one row for the status line
                numCols=floor(Editor.displayXPixels/fontW)
                self.mainTerminal=simpleTerminal(rows=numRows,columns=numCols, x=0, y=0, font=myFont, cursorDisplay=True)

                # create another highlighted terminal for the status line
                yStatusLine=self.mainTerminal.pixelHeight+1 # the status line y-position is just below the upper main terminal
                # instance the status terminal, cursorDisplay is OFF
                self.statusTerminal=simpleTerminal(rows=1,columns=40, y=yStatusLine, textColor=0x000000, bgColor=0xFFFFFF, cursorDisplay=False)

                self.g=displayio.Group(max_size=2, scale=1)
                Editor.display.show(self.g) #
                self.g.append(self.mainTerminal.displayGroup)
                self.g.append(self.statusTerminal.displayGroup)

    def goto(self, rowx, coly):
        if Editor.displayOutput:
            self.mainTerminal.setCursor(coly,rowx)
        else:
            self.wr("\x1b[{};{}H".format(rowx + 1, coly + 1))
    def clear_to_eol(self):
        if Editor.displayOutput:
            self.mainTerminal.clearEOL()
        else:
            self.wr("\x1b[0K")
    def cursor(self, onoff): # alternate the color of the cursor
        if Editor.displayOutput:
            if onoff:
                self.mainTerminal.cursorOn()
            else:
                self.mainTerminal.cursorOff()
        else:
            self.wr("\x1b[?25h" if onoff else "\x1b[?25l")

    def hilite(self, mode):
        if Editor.displayOutput:
            pass # No highlight function with external display
        else:
            if mode == 1:
                self.wr("\x1b[1;37;46m")
            elif mode == 2:
                self.wr("\x1b[43m")
            else:
                self.wr("\x1b[0m")

    def mouse_reporting(self, onoff):
        if Editor.displayOutput:
            pass
        else:
            self.wr('\x1b[?9h' if onoff else '\x1b[?9l')

    def scroll_region(self, stop):
        if Editor.displayOutput:
            pass # unnecessary for this display
        else:
            self.wr('\x1b[1;{}r'.format(stop) if stop else '\x1b[r')

    def scroll_up(self, scrolling):
        if Editor.displayOutput:
            Editor.display.auto_refresh=False
            for i in range(0, scrolling):
                self.mainTerminal.scrollUp()
            Editor.display.auto_refresh=True
        else:
            Editor.scrbuf[scrolling:] = Editor.scrbuf[:-scrolling]
            Editor.scrbuf[:scrolling] = [''] * scrolling
            self.goto(0, 0)
            self.wr("\x1bM" * scrolling)
    def scroll_down(self, scrolling):
        if Editor.displayOutput:
            Editor.display.auto_refresh=False
            for i in range(0, scrolling):
                self.mainTerminal.scrollDown()
            Editor.display.auto_refresh=True
        else:
            Editor.scrbuf[:-scrolling] = Editor.scrbuf[scrolling:]
            Editor.scrbuf[-scrolling:] = [''] * scrolling
            self.goto(Editor.height - 1, 0)
            self.wr("\n" * scrolling)
    def get_screen_size(self):
        if Editor.displayOutput:
            displayRows=self.mainTerminal.rows+self.statusTerminal.rows
            displayColumns=self.mainTerminal.columns
            screenSize=[displayRows, displayColumns]
            return screenSize
        else:
            self.wr('\x1b[999;999H\x1b[6n')
            pos = ''

            char=self.rd_raw()
            while char != 'R':
                pos += char
                char = self.rd_raw()
            return [int(i, 10) for i in pos.lstrip("\n\x1b[").split(';')]


    def redraw(self, flag):
        if Editor.displayOutput:
            Editor.display.auto_refresh=False # turn off refresh for now
            Editor.display.show(self.g)
        self.cursor(False)
        Editor.height, Editor.width = self.get_screen_size()
        Editor.height -= 1
        Editor.scrbuf = [(False,"\x00")] * Editor.height
        self.row = min(Editor.height - 1, self.row)
        self.scroll_region(Editor.height)
        self.mouse_reporting(True)
        if flag:
            self.message = PYE_VERSION
        if is_linux and not is_micropython:
            signal.signal(signal.SIGWINCH, Editor.signal_handler)
        if is_micropython:
            gc.collect()
            #if flag:
            #    self.message += "{} Bytes Memory available".format(gc.mem_free())
            #print("\n here {} Bytes Memory available".format(gc.mem_free()))
        self.changed = '' if self.hash == self.hash_buffer() else '*'

        if Editor.displayOutput:
            Editor.display.auto_refresh=True # turn display refresh back on
    def get_input(self):
        while True:
            in_buffer = self.rd()
            if in_buffer == '\x1b':
                while True:
                    in_buffer += self.rd()
                    c = in_buffer[-1]
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
                if len(in_buffer) == 2 and c.isalpha():
                    in_buffer = chr(ord(in_buffer[1]) & 0x1f)
            if in_buffer in self.KEYMAP:
                c = self.KEYMAP[in_buffer]
                if c != KEY_MOUSE:
                    return c, None
                else:
                    mouse_fct = ord(self.rd_raw())
                    mouse_x = ord(self.rd_raw()) - 33
                    mouse_y = ord(self.rd_raw()) - 33
                    if mouse_fct == 0x61:
                        return KEY_SCRLDN, 3
                    elif mouse_fct == 0x60:
                        return KEY_SCRLUP, 3
                    else:
                        return KEY_MOUSE, [mouse_x, mouse_y, mouse_fct]
            elif ord(in_buffer[0]) >= 32:
                return KEY_NONE, in_buffer
    def display_window(self):
        if Editor.displayOutput:
            self.display.auto_refresh=False # turn off refresh for now
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
        self.vcol = max(0, min(self.col, len(self.content[self.cur_line])))
        if self.vcol >= Editor.width + self.margin:
            self.margin = self.vcol - Editor.width + (Editor.width >> 2)
        elif self.vcol < self.margin:
            self.margin = max(self.vcol - (Editor.width >> 2), 0)
        if not (self.top_line <= self.cur_line < self.top_line + Editor.height):
            self.top_line = max(self.cur_line - self.row, 0)
        self.row = self.cur_line - self.top_line
        self.cursor(False)
        line = self.top_line
        if self.mark is None:
            flag = 0
        else:
            start_line, start_col, end_line, end_col = self.mark_range()
            start_col = max(start_col - self.margin, 0)
            end_col = max(end_col - self.margin, 0)
        for c in range(Editor.height):
            if line == self.total_lines:
                if Editor.scrbuf[c] != (False,''):
                    self.goto(c, 0)
                    self.clear_to_eol()
                    Editor.scrbuf[c] = (False,'')
            else:
                if self.mark is not None:
                    flag = ((start_line <= line < end_line) +
                            ((start_line == line) << 1) +
                            (((end_line - 1) == line) << 2))
                l = (flag,
                     self.content[line][self.margin:self.margin + Editor.width])
                if (flag and line == self.cur_line) or l != Editor.scrbuf[c]:
                    self.goto(c, 0)
                    if flag == 0:
                        self.wr(l[1])
                    elif flag == 7:
                        self.wr(l[1][:start_col])
                        self.hilite(2)
                        self.wr(l[1][start_col:end_col])
                        self.hilite(0)
                        self.wr(l[1][end_col:])
                    elif flag == 3:
                        self.wr(l[1][:start_col])
                        self.hilite(2)
                        self.wr(l[1][start_col:])
                        self.wr(' ')
                        self.hilite(0)
                    elif flag == 5:
                        self.hilite(2)
                        self.wr(l[1][:end_col])
                        self.hilite(0)
                        self.wr(l[1][end_col:])
                    else:
                        self.hilite(2)
                        self.wr(l[1])
                        self.wr(' ')
                        self.hilite(0)
                    if len(l[1]) < Editor.width:
                        self.clear_to_eol()
                    Editor.scrbuf[c] = l
                line += 1
        self.goto(Editor.height, 0)
        self.hilite(1)
        statusString=("{}{} Row: {}/{} Col: {}  {}".format(
            self.changed, self.fname, self.cur_line + 1, self.total_lines,
            self.vcol + 1, self.message)[:self.width - 1])
        if Editor.displayOutput:
            self.statusTerminal.setCursor(0,0)
            self.statusTerminal.write(statusString)
            self.statusTerminal.clearEOL()

        else:
            self.wr(statusString)
            self.clear_to_eol()
            self.hilite(0)
        self.goto(self.row, self.vcol - self.margin)
        self.cursor(True)

        if Editor.displayOutput:
            self.display.auto_refresh=True # turn display refresh back on
    def spaces(self, line, pos = None):
        return (len(line) - len(line.lstrip(" ")) if pos is None else
                len(line[:pos]) - len(line[:pos].rstrip(" ")))
    def mark_range(self):
        if self.mark[0] == self.cur_line:
            return ((self.cur_line, self.mark[1], self.cur_line + 1, self.col)
                    if self.mark[1] < self.col else
                    (self.cur_line, self.col, self.cur_line + 1, self.mark[1]))
        else:
            return ((self.mark[0], self.mark[1], self.cur_line + 1, self.col)
                    if self.mark[0] < self.cur_line else
                    (self.cur_line, self.col, self.mark[0] + 1, self.mark[1]))
    def line_range(self):
        res = self.mark_range()
        return (res[0], res[2]) if res[3] > 0 else (res[0], res[2] - 1)
    def line_edit(self, prompt, default, zap=None):
        if Editor.displayOutput:
            push_msg = lambda msg: self.statusTerminal.write(msg + "\b" * len(msg))
        else:
            push_msg = lambda msg: self.wr(msg + "\b" * len(msg))
        if Editor.displayOutput:
            self.statusTerminal.setCursor(0,0)
            self.statusTerminal.write(prompt)
            self.statusTerminal.write(default)
            self.statusTerminal.clearEOL()
        else:
            self.goto(Editor.height, 0)
            self.hilite(1)
            self.wr(prompt)
            self.wr(default)
            self.clear_to_eol()
        res = default
        pos = len(res)
        while True:
            key, char = self.get_input()
            if key == KEY_NONE:
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + char + res[pos:]
                    if Editor.displayOutput:
                        self.statusTerminal.write(res[pos])
                    else:
                        self.wr(res[pos])
                    pos += len(char)
                    push_msg(res[pos:])
            elif key in (KEY_ENTER, KEY_TAB):
                self.hilite(0)
                return res
            elif key in (KEY_QUIT, KEY_COPY):
                self.hilite(0)
                return None
            elif key == KEY_LEFT:
                if pos > 0:
                    if Editor.displayOutput:
                        self.statusTerminal.write("\b")
                    else:
                        self.wr("\b")
                    pos -= 1
            elif key == KEY_RIGHT:
                if pos < len(res):
                    if Editor.displayOutput:
                        self.statusTerminal.write(res[pos])
                    else:
                        self.wr(res[pos])
                    pos += 1
            elif key == KEY_HOME:
                if Editor.displayOutput:
                    self.statusTerminal.write("\b" * pos)
                else:
                    self.wr("\b" * pos)
                pos = 0
            elif key == KEY_END:
                if Editor.displayOutput:
                    self.statusTerminal.write(res[pos:])
                else:
                    self.wr(res[pos:])
                pos = len(res)
            elif key == KEY_DELETE:  
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ')
            elif key == KEY_BACKSPACE:
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    if Editor.displayOutput:
                        self.statusTerminal.write("\b")
                    else:
                        self.wr("\b")
                    pos -= 1
                    push_msg(res[pos:] + ' ')
            elif key == KEY_PASTE:
                if Editor.displayOutput:
                    self.statusTerminal.write('\b' * pos + ' ' * len(res) + '\b' * len(res))
                else:
                    self.wr('\b' * pos + ' ' * len(res) + '\b' * len(res))
                res = self.getsymbol(self.content[self.cur_line], self.col, zap)
                if Editor.displayOutput:
                    self.statusTerminal.write(res)
                else:
                    self.wr(res)
                pos = len(res)
    def getsymbol(self, s, pos, zap):
        if pos < len(s) and zap is not None:
            start = self.skip_while(s, pos, zap, -1)
            stop = self.skip_while(s, pos, zap, 1)
            return s[start+1:stop]
        else:
            return ''
    def issymbol(self, c, zap):
        return c.isalpha() or c.isdigit() or c in zap
    def skip_until(self, s, pos, zap, way):
        stop = -1 if way < 0 else len(s)
        while pos != stop and not self.issymbol(s[pos], zap):
            pos += way
        return pos
    def skip_while(self, s, pos, zap, way):
        stop = -1 if way < 0 else len(s)
        while pos != stop and self.issymbol(s[pos], zap):
            pos += way
        return pos
    def move_up(self):
        if self.cur_line > 0:
            self.cur_line -= 1
            if self.cur_line < self.top_line:
                self.scroll_up(1)
    def skip_up(self):
        if self.col == 0 and self.cur_line > 0:
            self.col = len(self.content[self.cur_line - 1])
            self.move_up()
            return True
        else:
            return False
    def move_left(self):
        self.col = self.vcol
        if not self.skip_up():
            self.col -= 1
    def move_down(self):
        if self.cur_line < self.total_lines - 1:
            self.cur_line += 1
            if self.cur_line == self.top_line + Editor.height:
                self.scroll_down(1)
    def skip_down(self, l):
        if self.col >= len(l) and self.cur_line < self.total_lines - 1:
            self.col = 0
            self.move_down()
            return True
        else:
            return False
    def move_right(self, l):
        if not self.skip_down(l):
            self.col += 1
    def find_in_file(self, pattern, col, end):
        Editor.find_pattern = pattern
        if Editor.case != "y":
            pattern = pattern.lower()
        try:
            rex = re_compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return None
        start = self.cur_line
        if (col > len(self.content[start]) or
            (pattern[0] == '^' and col != 0)):
            start, col = start + 1, 0
        for line in range(start, end):
            l = self.content[line][col:]
            if Editor.case != "y":
                l = l.lower()
            match = rex.search(l)
            if match:
                self.cur_line = line
                if pattern[-1:] == "$" and match.group(0)[-1:] != "$":
                    self.col = col + len(l) - len(match.group(0))
                else:
                    self.col = col + l.find(match.group(0))
                return len(match.group(0))
            col = 0
        else:
            self.message = pattern + " not found (again)"
            return None
    def undo_add(self, lnum, text, key, span = 1, chain=False):
        self.changed = '*'
        if (len(self.undo) == 0 or key == KEY_NONE or
            self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit:
                del self.undo[0]
            self.undo.append([lnum, span, text, key, self.col, chain])
            self.redo = []
    def undo_redo(self, undo, redo):
        chain = True
        redo_start = len(redo)
        while len(undo) > 0 and chain:
            action = undo.pop()
            if not action[3] in (KEY_INDENT, KEY_DEDENT, KEY_COMMENT):
                self.cur_line = action[0]
            self.col = action[4]
            if len(redo) >= self.undo_limit:
                del redo[0]
            if action[1] >= 0:
                if action[1] == 0:
                    redo.append(action[0:1] + [-len(action[2]), None] + action[3:])
                else:
                    redo.append(action[0:1] + [len(action[2])] +
                        [self.content[action[0]:action[0] + action[1]]] + action[3:])
                if action[0] < self.total_lines:
                    self.content[action[0]:action[0] + action[1]] = action[2]
                else:
                    self.content += action[2]
            else:
                redo.append(action[0:1] + [0] +
                    [self.content[action[0]:action[0] - action[1]]] + action[3:])
                del self.content[action[0]:action[0] - action[1]]
            chain = action[5]
        if (len(redo) - redo_start) > 0:
            redo[-1][5] = True
            redo[redo_start][5] = False
            self.total_lines = len(self.content)
            self.changed = '' if self.hash == self.hash_buffer() else '*'
            self.mark = None
    def set_mark(self):
        if self.mark is None:
            self.mark = (self.cur_line, self.col)
    def yank_mark(self):
        start_row, start_col, end_row, end_col = self.mark_range()
        Editor.yank_buffer = self.content[start_row:end_row]
        Editor.yank_buffer[-1] = Editor.yank_buffer[-1][:end_col]
        Editor.yank_buffer[0] = Editor.yank_buffer[0][start_col:]
    def delete_mark(self, yank):
        if yank:
            self.yank_mark()
        start_row, start_col, end_row, end_col = self.mark_range()
        self.undo_add(start_row, self.content[start_row:end_row], KEY_NONE, 1, False)
        self.content[start_row] = self.content[start_row][:start_col] + self.content[end_row - 1][end_col:]
        if start_row + 1 < end_row:
            del self.content[start_row + 1:end_row]
        self.col = start_col
        if self.content == []:
            self.content = [""]
            self.undo[-1][1] = 1
        self.total_lines = len(self.content)
        self.cur_line = start_row
        self.mark = None
    def handle_edit_keys(self, key, char):
        l = self.content[self.cur_line]
        if key == KEY_NONE:
            self.col = self.vcol
            if self.mark is not None:
                self.delete_mark(False)
                l = self.content[self.cur_line]
                chain = True
            else:
                chain = False
            self.undo_add(self.cur_line, [l], 0x20 if char == " " else 0x41, 1, chain)
            self.content[self.cur_line] = l[:self.col] + char + l[self.col:]
            self.col += len(char)
        elif key == KEY_SHIFT_CTRL_LEFT:
            self.set_mark()
            key = KEY_WORD_LEFT
        elif key == KEY_SHIFT_CTRL_RIGHT:
            self.set_mark()
            key = KEY_WORD_RIGHT
        if key == KEY_DOWN:
             self.move_down()
        elif key == KEY_UP:
            self.move_up()
        elif key == KEY_LEFT:
            self.move_left()
        elif key == KEY_RIGHT:
            self.move_right(l)
        elif key == KEY_WORD_LEFT:
            self.col = self.vcol
            if self.skip_up():
                l = self.content[self.cur_line]
            pos = self.skip_until(l, self.col - 1, self.word_char, -1)
            self.col = self.skip_while(l, pos, self.word_char, -1) + 1
        elif key == KEY_WORD_RIGHT:
            if self.skip_down(l):
                l = self.content[self.cur_line]
            pos = self.skip_until(l, self.col, self.word_char, 1)
            self.col = self.skip_while(l, pos, self.word_char, 1)
        elif key == KEY_DELETE:
            self.col = self.vcol
            if self.mark is not None:
                self.delete_mark(False)
            elif self.col < len(l):
                self.undo_add(self.cur_line, [l], KEY_DELETE)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines:
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], KEY_NONE)
                self.content[self.cur_line] = l + (
                    self.content.pop(self.cur_line + 1).lstrip()
                    if Editor.autoindent == "y" and self.col > 0
                    else self.content.pop(self.cur_line + 1))
                self.total_lines -= 1
        elif key == KEY_BACKSPACE:
            self.col = self.vcol
            if self.mark is not None:
                self.delete_mark(False)
            elif self.col > 0:
                self.undo_add(self.cur_line, [l], KEY_BACKSPACE)
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
            elif self.cur_line > 0:
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], KEY_NONE)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += self.content.pop(self.cur_line)
                self.cur_line -= 1
                self.total_lines -= 1
        elif key == KEY_DEL_WORD:
            if self.col < len(l):
                pos = self.skip_while(l, self.col, self.word_char, 1)
                pos += self.spaces(l[pos:])
                if self.col < pos:
                    self.undo_add(self.cur_line, [l], KEY_DEL_WORD)
                    self.content[self.cur_line] = l[:self.col] + l[pos:]
        elif key == KEY_HOME:
            self.col = self.spaces(l) if self.col == 0 else 0
        elif key == KEY_END:
            ni = len(l.split(Editor.comment_char.strip())[0].rstrip())
            ns = self.spaces(l)
            self.col = ni if self.col >= len(l) and ni > ns else len(l)
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
        elif key == KEY_GOTO:
            line = self.line_edit("Goto Line: ", "")
            if line:
                self.cur_line = int(line) - 1
                self.row = Editor.height >> 1
        elif key == KEY_FIRST:
            self.cur_line = 0
        elif key == KEY_LAST:
            self.cur_line = self.total_lines - 1
            self.row = Editor.height - 1
        elif key == KEY_TOGGLE:
            pat = self.line_edit("Autoindent {}, Search Case {}"
            ", Tabsize {}, Comment {}, Tabwrite {}: ".format(
            Editor.autoindent, Editor.case, self.tab_size, Editor.comment_char, self.write_tabs), "")
            try:
                res = [i.lstrip().lower() for i in pat.split(",")]
                if res[0]: Editor.autoindent = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: Editor.case = 'y' if res[1][0] == 'y' else 'n'
                if res[2]: self.tab_size = int(res[2])
                if res[3]: Editor.comment_char = res[3]
                if res[4]: self.write_tabs = 'y' if res[4][0] == 'y' else 'n'
            except:
                pass
        elif key == KEY_MOUSE:
            if char[1] < Editor.height:
                self.col = char[0] + self.margin
                self.cur_line = char[1] + self.top_line
                if char[2] in (0x22, 0x30):
                    self.mark = (self.cur_line, self.col) if self.mark is None else None
        elif key == KEY_SCRLUP:
            ni = 1 if char is None else 3
            if self.top_line > 0:
                self.top_line = max(self.top_line - ni, 0)
                self.cur_line = min(self.cur_line, self.top_line + Editor.height - 1)
                self.scroll_up(ni)
        elif key == KEY_SCRLDN:
            ni = 1 if char is None else 3
            if self.top_line + Editor.height < self.total_lines:
                self.top_line = min(self.top_line + ni, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scroll_down(ni)
        elif key == KEY_MATCH:
            if self.col < len(l):
                brackets = "<{[()]}>"
                srch = l[self.col]
                i = brackets.find(srch)
                if i >= 0:
                    match = brackets[7 - i]
                    level = 0
                    way = 1 if i < 4 else -1
                    i = self.cur_line
                    c = self.col + way
                    lstop = self.total_lines if way > 0 else -1
                    while i != lstop:
                        cstop = len(self.content[i]) if way > 0 else -1
                        while c != cstop:
                            if self.content[i][c] == match:
                                if level == 0:
                                    self.cur_line, self.col = i, c
                                    return
                                else:
                                    level -= 1
                            elif self.content[i][c] == srch:
                                level += 1
                            c += way
                        i += way
                        c = 0 if way > 0 else len(self.content[i]) - 1
                    self.message = "No match"
        elif key == KEY_MARK:
            if self.mark is None:
                self.mark = (self.cur_line, self.col)
                self.move_right(l)
            else:
                self.mark = None
        elif key == KEY_SHIFT_DOWN:
            self.set_mark()
            self.move_down()
        elif key == KEY_SHIFT_UP:
            self.set_mark()
            self.move_up()
        elif key == KEY_SHIFT_LEFT:
            self.set_mark()
            self.move_left()
        elif key == KEY_SHIFT_RIGHT:
            self.set_mark()
            self.move_right(l)
        elif key == KEY_ALT_UP:
            if self.mark is None:
                start_line = self.cur_line
                end_line = start_line + 1
            else:
                start_line, end_line = self.line_range()
                if start_line > 0:
                    self.mark = (self.mark[0] - 1, self.mark[1])
            if start_line > 0:
                self.undo_add(start_line - 1, self.content[start_line - 1:end_line],
                              KEY_NONE, end_line - start_line + 1)
                self.content[start_line - 1:end_line - 1], self.content[end_line - 1] = (
                    self.content[start_line:end_line], self.content[start_line - 1])
                self.move_up()
        elif key == KEY_ALT_DOWN:
            if self.mark is None:
                start_line = self.cur_line
                end_line = start_line + 1
            else:
                start_line, end_line = self.line_range()
                if end_line < self.total_lines:
                    self.mark = (self.mark[0] + 1, self.mark[1])
                    if self.cur_line == end_line == (self.total_lines - 1):
                        self.move_left()
            if end_line < self.total_lines:
                self.undo_add(start_line, self.content[start_line:end_line + 1],
                              KEY_NONE, end_line - start_line + 1)
                self.content[start_line + 1:end_line + 1], self.content[start_line] = (
                    self.content[start_line:end_line], self.content[end_line])
                self.move_down()
        elif key == KEY_ENTER:
            self.col = self.vcol
            self.mark = None
            self.undo_add(self.cur_line, [l], KEY_NONE, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if Editor.autoindent == "y":
                ni = min(self.spaces(l), self.col)
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == KEY_TAB:
            if self.mark is None:
                self.col = self.vcol
                self.undo_add(self.cur_line, [l], KEY_TAB)
                ni = self.tab_size - self.col % self.tab_size
                self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
                self.col += ni
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_INDENT, lrange[1] - lrange[0])
                for i in range(lrange[0],lrange[1]):
                    if len(self.content[i]) > 0:
                        self.content[i] = ' ' * (self.tab_size - self.spaces(self.content[i]) % self.tab_size) + self.content[i]
        elif key == KEY_BACKTAB:
            if self.mark is None:
                self.col = self.vcol
                ni = min((self.col - 1) % self.tab_size + 1, self.spaces(l, self.col))
                if ni > 0:
                    self.undo_add(self.cur_line, [l], KEY_BACKTAB)
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
            else:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_DEDENT, lrange[1] - lrange[0])
                for i in range(lrange[0],lrange[1]):
                    ns = self.spaces(self.content[i])
                    if ns > 0:
                        self.content[i] = self.content[i][(ns - 1) % self.tab_size + 1:]
        elif key == KEY_REPLC:
            count = 0
            pat = self.line_edit("Replace: ", Editor.find_pattern, "_")
            if pat:
                rpat = self.line_edit("With: ", Editor.replc_pattern, "_")
                if rpat is not None:
                    Editor.replc_pattern = rpat
                    q = ''
                    cur_line, cur_col = self.cur_line, self.col
                    if self.mark is not None:
                        (self.cur_line, self.col, end_line, end_col) = self.mark_range()
                    else:
                        end_line = self.total_lines
                        end_col = 999999
                    self.message = "Replace (yes/No/all/quit) ? "
                    chain = False
                    while True:
                        ni = self.find_in_file(pat, self.col, end_line)
                        if ni is not None and (self.cur_line != (end_line - 1) or self.col < end_col):
                            if q != 'a':
                                self.display_window()
                                key, char = self.get_input()
                                q = char.lower()
                            if q == 'q' or key == KEY_QUIT:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], KEY_NONE, 1, chain)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat) + (ni == 0)
                                count += 1
                                chain = True
                            else:
                                 self.col += 1
                        else:
                            break
                    self.cur_line, self.col = cur_line, cur_col
                    self.message = "'{}' replaced {} times".format(pat, count)
        elif key == KEY_CUT:
            if self.mark is not None:
                self.delete_mark(True)
        elif key == KEY_COPY:
            if self.mark is not None:
                self.yank_mark()
                self.mark = None
        elif key == KEY_PASTE:
            if Editor.yank_buffer:
                self.col = self.vcol
                if self.mark is not None:
                    self.delete_mark(False)
                    chain = True
                else:
                    chain = False
                head, tail = Editor.yank_buffer[0], Editor.yank_buffer[-1]
                Editor.yank_buffer[0] = self.content[self.cur_line][:self.col] + Editor.yank_buffer[0]
                Editor.yank_buffer[-1] += self.content[self.cur_line][self.col:]
                if len(Editor.yank_buffer) > 1:
                    self.undo_add(self.cur_line, None, KEY_NONE, -len(Editor.yank_buffer) + 1, chain)
                else:
                    self.undo_add(self.cur_line, [self.content[self.cur_line]], KEY_NONE, 1, chain)
                self.content[self.cur_line:self.cur_line + 1] = Editor.yank_buffer
                Editor.yank_buffer[-1], Editor.yank_buffer[0] = tail, head
                self.total_lines = len(self.content)
        elif key == KEY_WRITE:
            fname = self.line_edit("Save File: ", self.fname, "_.-")
            if fname:
                self.put_file(fname)
                self.fname = fname
                self.hash = self.hash_buffer()
                self.changed = ''
        elif key == KEY_UNDO:
            self.undo_redo(self.undo, self.redo)
        elif key == KEY_REDO:
            self.undo_redo(self.redo, self.undo)
        elif key == KEY_COMMENT:
            if self.mark is None:
                lrange = (self.cur_line, self.cur_line + 1)
            else:
                lrange = self.line_range()
            self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], KEY_COMMENT, lrange[1] - lrange[0])
            ni = len(Editor.comment_char)
            for i in range(lrange[0],lrange[1]):
                if self.content[i].strip() != "":
                    ns = self.spaces(self.content[i])
                    if self.content[i][ns:ns + ni] == Editor.comment_char:
                        self.content[i] = ns * " " + self.content[i][ns + ni:]
                    else:
                        self.content[i] = ns * " " + Editor.comment_char + self.content[i][ns:]
        elif key == KEY_REDRAW:
            self.redraw(True)
    def edit_loop(self):
        if not self.content:
            self.content = [""]
        self.total_lines = len(self.content)
        os.chdir(self.work_dir)
        self.redraw(self.message == "")
        while True:
            self.display_window() 
            key, char = self.get_input()
            self.message = ''
            if key == KEY_QUIT:
                if self.hash != self.hash_buffer():
                    res = self.line_edit("Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                if Editor.displayOutput:
                    self.statusTerminal.setCursor(0,0)
                    self.statusTerminal.clearEOL()
                else:
                    self.scroll_region(0)
                    self.mouse_reporting(False)
                    self.goto(Editor.height, 0)
                    self.clear_to_eol()
                self.undo = []
                return key
            elif key == KEY_NEXT:
                return key
            elif key == KEY_GET:
                if self.mark is not None:
                    self.mark = None
                    self.display_window()
                return key
            else:
                self.handle_edit_keys(key, char)
    def packtabs(self, s):
        sb = StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if (len(c) - len(cr)) > 1:
                sb.write(cr + "\t")
            else:
                sb.write(c)
        return sb.getvalue()
    def hash_buffer(self):
        res = 0
        for line in self.content:
            res = ((res * 17 + 1) ^ hash(line)) & 0x3fffffff
        return res
    def get_file(self, fname):
        if fname:
            try:
                self.fname = fname
                if fname in ('.', '..') or (os.stat(fname)[0] & 0x4000):
                    os.chdir(fname)
                    self.work_dir = os.getcwd()
                    self.fname = "/" if self.work_dir == "/" else self.work_dir.split("/")[-1]
                    self.content = ["Directory '{}'".format(self.work_dir), ""] + sorted(os.listdir('.'))
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
            except OSError:
                self.message = "Error: file '" + fname + "' may not exist"
        self.hash = self.hash_buffer()
    def put_file(self, fname):
        tmpfile = fname + ".pyetmp"
        with open(tmpfile, "w") as f:
            for l in self.content:
                if self.write_tabs == 'y':
                    f.write(self.packtabs(l) + '\n')
                else:
                    f.write(l + '\n')
        try:
            os.remove(fname)
        except:
            pass
        os.rename(tmpfile, fname)
def expandtabs(s):
    if '\t' in s:
        sb = StringIO()
        pos = 0
        for c in s:
            if c == '\t':
                sb.write(" " * (8 - pos % 8))
                pos += 8 - pos % 8
            else:
                sb.write(c)
                pos += 1
        return sb.getvalue(), True
    else:
        return s, False

def init_display():
    if Editor.displayOutput:
        import fontio, displayio, terminalio
        from adafruit_st7789 import ST7789
        displayio.release_displays()

        spi = board.SPI()
        spi = board.SPI()
        tft_cs = board.D12 # arbitrary, pin not used for my display
        tft_dc = board.D2
        tft_backlight = board.D4
        tft_reset=board.D3

        while not spi.try_lock():
            pass
        spi.unlock()

        display_bus = displayio.FourWire(
            spi,
            command=tft_dc,
            chip_select=tft_cs,
            reset=tft_reset,
            baudrate=24000000,
            polarity=1,
            phase=1,
        )

        Editor.display = ST7789(display_bus, width=Editor.displayXPixels, height=Editor.displayYPixels, rotation=0, rowstart=80, colstart=0)

        Editor.display.show(None)

def deinit_display():  #This belongs at the root, should be done only once for each time "pye" is executed.
    if Editor.displayOutput:
        Editor.display.show(None)

def init_tty(device):  # This belongs at the root, should be done only once for each time "pye" is executed.
    if Editor.inputUART:
        ##### Modified for UART input
        Editor.uart = busio.UART(board.TX, board.RX, baudrate=115200, timeout=0.1, receiver_buffer_size=64)
        if Editor.displayOutput:
            Editor.rd_raw_fct=Editor.rd 
        else:
            if hasattr(sys.stdin, "buffer"):
                Editor.rd_raw_fct = sys.stdin.buffer.read
            else:
                Editor.rd_raw_fct = sys.stdin.read

    else:
        try:
            from micropython import kbd_intr
            kbd_intr(-1)
        except ImportError:
            pass
        if hasattr(sys.stdin, "buffer"):
            Editor.rd_raw_fct = sys.stdin.buffer.read
        else:
            Editor.rd_raw_fct = sys.stdin.read


def deinit_tty():
    if Editor.inputUART:
        Editor.uart.deinit()
    try:
        from micropython import kbd_intr
        kbd_intr(3)
    except ImportError:
        pass

def pye(*content, tab_size=4, undo=50, device=0):
    gc.collect()
    index = 0
    undo = max(4, (undo if type(undo) is int else 0))
    current_dir = os.getcwd()

    init_display() # setup the display, if required.

    if content:
        slot = []
        for f in content:
            slot.append(Editor(tab_size, undo))
            if type(f) == str and f:
                try:
                    slot[index].get_file(f)
                except Exception as err:
                    slot[index].message = "{!r}".format(err)
            else:
                try:
                    slot[index].content = [str(_) for _ in f]
                except:
                    slot[index].content = [str(f)]
            index += 1
    else:
        slot = [Editor(tab_size, undo)]
        slot[0].get_file(current_dir)

    init_tty(device) # Should be done once

    while True:
        try:
            index %= len(slot)
            key = slot[index].edit_loop()
            if key == KEY_QUIT:
                if len(slot) == 1:
                    break
                print('deleting index: {}'.format(index))
                del slot[index]
            elif key == KEY_GET:
                f = slot[index].line_edit("Open file: ", "", "_.-")
                if f is not None:
                        slot.append(Editor(tab_size, undo))
                        index = len(slot) - 1
                        slot[index].get_file(f)
                        print('3', end='')
            elif key == KEY_NEXT:
                        index += 1
                        print('4', end='')
        except Exception as err:
            print('ex')
            sys.print_exception(err)
            slot[index].message = "{!r}".format(err)
    deinit_tty()
    deinit_display()
    Editor.yank_buffer = []
    os.chdir(current_dir)
    return slot[0].content if (slot[0].fname == "") else slot[0].fname
