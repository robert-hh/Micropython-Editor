PYE_VERSION   = " V2.48m "
import sys
import gc
import os
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
KEY_NONE      = const(0x00)
KEY_UP        = const(0x0b)
KEY_DOWN      = const(0x0d)
KEY_LEFT      = const(0x1f)
KEY_RIGHT     = const(0x1e)
KEY_HOME      = const(0x10)
KEY_END       = const(0x03)
KEY_PGUP      = const(0xfff1)
KEY_PGDN      = const(0xfff2)
KEY_SHIFT_UP  = const(0xfff5)
KEY_SHIFT_DOWN= const(0xfff6)
KEY_SHIFT_LEFT= const(0xfff0)
KEY_SHIFT_RIGHT= const(0xffef)
KEY_QUIT      = const(0x11)
KEY_ENTER     = const(0x0a)
KEY_BACKSPACE = const(0x08)
KEY_DELETE    = const(0x7f)
KEY_DEL_WORD  = const(0xfff7)
KEY_WRITE     = const(0x13)
KEY_TAB       = const(0x09)
KEY_BACKTAB   = const(0x15)
KEY_FIND      = const(0x06)
KEY_GOTO      = const(0x07)
KEY_SCRLUP    = const(0x1c)
KEY_SCRLDN    = const(0x1d)
KEY_FIND_AGAIN= const(0x0e)
KEY_REDRAW    = const(0x05)
KEY_UNDO      = const(0x1a)
KEY_REDO      = const(0xffee)
KEY_CUT       = const(0x18)
KEY_PASTE     = const(0x16)
KEY_COPY      = const(0x04)
KEY_FIRST     = const(0x14)
KEY_LAST      = const(0x02)
KEY_REPLC     = const(0x12)
KEY_TOGGLE    = const(0x01)
KEY_GET       = const(0x0f)
KEY_MARK      = const(0x0c)
KEY_NEXT      = const(0x17)
KEY_INDENT    = const(0xfffe)
KEY_DEDENT    = const(0xffff)
class Editor:
    KEYMAP = {
    "\x1b[A" : KEY_UP,
    "\x1b[1;2A": KEY_SHIFT_UP,
    "\x1b[B" : KEY_DOWN,
    "\x1b[1;2B": KEY_SHIFT_DOWN,
    "\x1b[D" : KEY_LEFT,
    "\x1b[1;2D": KEY_SHIFT_LEFT,
    "\x1b[1;2C": KEY_SHIFT_RIGHT,
    "\x1b[C" : KEY_RIGHT,
    "\x1b[H" : KEY_HOME,
    "\x1bOH" : KEY_HOME,
    "\x1b[1~": KEY_HOME,
    "\x1b[F" : KEY_END,
    "\x1bOF" : KEY_END,
    "\x1b[4~": KEY_END,
    "\x1b[5~": KEY_PGUP,
    "\x1b[6~": KEY_PGDN,
    "\x03"   : KEY_COPY,
    "\r"     : KEY_ENTER,
    "\x7f"   : KEY_BACKSPACE,
    "\x1b[3~": KEY_DELETE,
    "\x1b[Z" : KEY_BACKTAB,
    "\x19"   : KEY_REDO,
    "\x08"   : KEY_REPLC,
    "\x12"   : KEY_REPLC,
    "\x11"   : KEY_QUIT,
    "\n"     : KEY_ENTER,
    "\x13"   : KEY_WRITE,
    "\x06"   : KEY_FIND,
    "\x0e"   : KEY_FIND_AGAIN,
    "\x07"   : KEY_GOTO,
    "\x05"   : KEY_REDRAW,
    "\x1a"   : KEY_UNDO,
    "\x09"   : KEY_TAB,
    "\x15"   : KEY_BACKTAB,
    "\x18"   : KEY_CUT,
    "\x16"   : KEY_PASTE,
    "\x04"   : KEY_COPY,
    "\x0c"   : KEY_MARK,
    "\x00"   : KEY_MARK,
    "\x14"   : KEY_FIRST,
    "\x02"   : KEY_LAST,
    "\x01"   : KEY_TOGGLE,
    "\x17"   : KEY_NEXT,
    "\x0f"   : KEY_GET,
    "\x1b[1;5H": KEY_FIRST,
    "\x1b[1;5F": KEY_LAST,
    }
    TERMCMD = [
        "\x1b[{row};{col}H",
        "\x1b[0K",
        "\x1b[?25h",
        "\x1b[?25l",
        "\x1b[0m",
        "\x1b[1;37;46m",
        "\x1b[43m",
        "\x1bM",
        "\n",
        '\x1b[1;{stop}r',
        '\x1b[r',
        "\b",
        "{chd}{file} Row: {row}/{total} Col: {col}  {msg}",
        "{chd}{file} {row}:{col}  {msg}",
    ]
    
    yank_buffer = []
    find_pattern = ""
    case = "n"
    autoindent = "y"
    replc_pattern = ""
    def __init__(self, tab_size, undo_limit, io_device):
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
        self.work_dir = os.getcwd()
        self.io_device = io_device
        self.wr = io_device.wr
    def goto(self, row, col):
        self.wr(self.TERMCMD[0].format(row=row + 1, col=col + 1))
    def clear_to_eol(self):
        self.wr(self.TERMCMD[1])
    def cursor(self, onoff):
        self.wr(self.TERMCMD[2] if onoff else self.TERMCMD[3])
    def hilite(self, mode):
        if mode == 1:
            self.wr(self.TERMCMD[5])
        elif mode == 2:
            self.wr(self.TERMCMD[6])
        else:
            self.wr(self.TERMCMD[4])
    def scroll_region(self, stop):
        self.wr(self.TERMCMD[9].format(stop=stop) if stop else self.TERMCMD[10])
    def scroll_up(self, scrolling):
        if self.TERMCMD[7]:
            Editor.scrbuf[scrolling:] = Editor.scrbuf[:-scrolling]
            Editor.scrbuf[:scrolling] = [''] * scrolling
            self.goto(0, 0)
            self.wr(self.TERMCMD[7] * scrolling)
    def scroll_down(self, scrolling):
        if self.TERMCMD[8]:
            Editor.scrbuf[:-scrolling] = Editor.scrbuf[scrolling:]
            Editor.scrbuf[-scrolling:] = [''] * scrolling
            self.goto(Editor.height - 1, 0)
            self.wr(self.TERMCMD[8] * scrolling)
    def redraw(self, flag):
        self.cursor(False)
        Editor.height, Editor.width = self.io_device.get_screen_size()
        Editor.height -= 1
        Editor.scrbuf = [(False,"\x00")] * Editor.height
        self.row = min(Editor.height - 1, self.row)
        self.scroll_region(Editor.height)
        if flag:
            self.message = PYE_VERSION
        if is_micropython:
            gc.collect()
            if flag:
                self.message += "{} Bytes Memory available".format(gc.mem_free())
        self.changed = '' if self.hash == self.hash_buffer() else '*'
    def get_input(self):
        while True:
            in_buffer = self.io_device.rd()
            if in_buffer == '\x1b':
                while True:
                    in_buffer += self.io_device.rd()
                    c = in_buffer[-1]
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
                if len(in_buffer) == 2 and c.isalpha():
                    in_buffer = chr(ord(in_buffer[1]) & 0x1f)
            if in_buffer in self.KEYMAP:
                c = self.KEYMAP[in_buffer]
                return c, None
            elif ord(in_buffer[0]) >= 32:
                return KEY_NONE, in_buffer
    def display_window(self):
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
        self.wr(self.TERMCMD[12 if Editor.width > 40 else 13].format(
            chd=self.changed, file=self.fname, row=self.cur_line + 1, total=self.total_lines,
            col=self.vcol + 1, msg=self.message)[:self.width - 1])
        self.clear_to_eol()
        self.hilite(0)
        self.goto(self.row, self.vcol - self.margin)
        self.cursor(True)
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
    def line_edit(self, prompt, default):
        push_msg = lambda msg: self.wr(msg + self.TERMCMD[11] * len(msg))
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
                    self.wr(self.TERMCMD[11])
                    pos -= 1
            elif key == KEY_RIGHT:
                if pos < len(res):
                    self.wr(res[pos])
                    pos += 1
            elif key == KEY_DELETE:
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ')
            elif key == KEY_BACKSPACE:
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr(self.TERMCMD[11])
                    pos -= 1
                    push_msg(res[pos:] + ' ')
            elif key == KEY_PASTE:
                if Editor.yank_buffer:
                    res += Editor.yank_buffer[0][:self.width - len(prompt) - pos - 1]
                    push_msg(res[pos:])
    def move_up(self):
        if self.cur_line > 0:
            self.cur_line -= 1
            if self.cur_line < self.top_line:
                self.scroll_up(1)
    def move_left(self):
        if self.col == 0 and self.cur_line > 0:
            self.col = len(self.content[self.cur_line - 1])
            self.move_up()
        else:
            self.col -= 1
    def move_down(self):
        if self.cur_line < self.total_lines - 1:
            self.cur_line += 1
            if self.cur_line == self.top_line + Editor.height:
                self.scroll_down(1)
    def move_right(self, l):
        if self.col >= len(l) and self.cur_line < self.total_lines - 1:
            self.col = 0
            self.move_down()
        else:
            self.col += 1
    def find_in_file(self, pattern, pos, end):
        Editor.find_pattern = pattern
        if Editor.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, end):
            if Editor.case != "y":
                match = self.content[line][spos:].lower().find(pattern)
            else:
                match = self.content[line][spos:].find(pattern)
            if match >= 0:
                self.col = match + spos
                self.cur_line = line
                return len(pattern)
            spos = 0
        else:
            self.message = "No match: " + pattern
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
        elif key == KEY_DOWN:
             self.move_down()
        elif key == KEY_UP:
            self.move_up()
        elif key == KEY_LEFT:
            self.move_left()
        elif key == KEY_RIGHT:
            self.move_right(l)
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
        elif key == KEY_HOME:
            self.col = self.spaces(l) if self.col == 0 else 0
        elif key == KEY_END:
            ni = len(l.split("\x23")[0].rstrip())
            ns = self.spaces(l)
            self.col = ni if self.col >= len(l) and ni > ns else len(l)
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
        elif key == KEY_GOTO:
            line = self.line_edit("Goto Line: ")
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
            ", Tabsize {}".format(
            Editor.autoindent, Editor.case, self.tab_size))
            try:
                res =  [i.lstrip().lower() for i in pat.split(",")]
                if res[0]: Editor.autoindent = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: Editor.case     = 'y' if res[1][0] == 'y' else 'n'
                if res[2]: self.tab_size = int(res[2])
            except:
                pass
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
            pat = self.line_edit("Replace: ", Editor.find_pattern)
            if pat:
                rpat = self.line_edit("With: ", Editor.replc_pattern)
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
            fname = self.line_edit("Save File: ", self.fname)
            if fname:
                self.put_file(fname)
                self.fname = fname
                self.hash = self.hash_buffer()
                self.changed = ''
        elif key == KEY_UNDO:
            self.undo_redo(self.undo, self.redo)
        elif key == KEY_REDO:
            self.undo_redo(self.redo, self.undo)
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
                    res = self.line_edit("File changed! Quit (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                self.scroll_region(0)
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
                    for i, l in enumerate(self.content):
                        self.content[i], tf = expandtabs(l.rstrip('\r\n\t '))
            except OSError:
                self.message = "Error: file '" + fname + "' may not exist"
        self.hash = self.hash_buffer()
    def put_file(self, fname):
        tmpfile = fname + ".pyetmp"
        with open(tmpfile, "w") as f:
            for l in self.content:
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
def pye_edit(*content, tab_size=4, undo=50, io_device=None):
    if io_device is None:
        print("IO device not defined")
        return
    gc.collect()
    index = 0
    undo = max(4, (undo if type(undo) is int else 0))
    current_dir = os.getcwd()
    if content:
        slot = []
        for f in content:
            slot.append(Editor(tab_size, undo, io_device))
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
        slot = [Editor(tab_size, undo, io_device)]
        slot[0].get_file(current_dir)
    while True:
        try:
            index %= len(slot)
            key = slot[index].edit_loop()
            if key == KEY_QUIT:
                if len(slot) == 1:
                    break
                del slot[index]
            elif key == KEY_GET:
                f = slot[index].line_edit("Open file: ", "")
                if f is not None:
                    slot.append(Editor(tab_size, undo,io_device))
                    index = len(slot) - 1
                    slot[index].get_file(f)
            elif key == KEY_NEXT:
                index += 1
        except Exception as err:
            slot[index].message = "{!r}".format(err)
            raise
    Editor.yank_buffer = []
    os.chdir(current_dir)
    return slot[0].content if (slot[0].fname == "") else slot[0].fname
import sys
class IO_DEVICE:
    def __init__(self):
        try:
            from micropython import kbd_intr
            kbd_intr(-1)
        except ImportError:
            pass
    def wr(self, s):
        sys.stdout.write(s)
    def rd(self):
        return sys.stdin.read(1)
    def deinit_tty(self):
        try:
            from micropython import kbd_intr
            kbd_intr(3)
        except ImportError:
            pass
    def get_screen_size(self):
        self.wr('\x1b[999;999H\x1b[6n')
        pos = ''
        char = self.rd()
        while char != 'R':
            pos += char
            char = self.rd()
        return [int(i, 10) for i in pos.lstrip("\n\x1b[").split(';')]
if "pye_edit" not in globals().keys():
    from pye import pye_edit
def pye(*args, tab_size=4, undo=50):
    io_device = IO_DEVICE()
    ret = pye_edit(*args, tab_size=tab_size, undo=undo, io_device=io_device)
    io_device.deinit_tty()
    return ret
