import sys, gc
class Editor:
    KEYMAP = { 
    b"\x1b[A" : 0x0b,
    b"\x1b[B" : 0x0d,
    b"\x1b[D" : 0x1f,
    b"\x1b[C" : 0x1e,
    b"\x1b[H" : 0x10, 
    b"\x1bOH" : 0x10, 
    b"\x1b[1~": 0x10, 
    b"\x1b[F" : 0x03, 
    b"\x1bOF" : 0x03, 
    b"\x1b[4~": 0x03, 
    b"\x1b[5~": 0x17,
    b"\x1b[6~": 0x19,
    b"\x03" : 0x11, 
    b"\r" : 0x0a,
    b"\x7f" : 0x08, 
    b"\x1b[3~": 0x7f,
    b"\x1b[Z" : 0x15, 
    }
    def __init__(self, tab_size, undo_limit):
        self.top_line = self.cur_line = self.row = self.col = self.margin = 0
        self.tab_size = tab_size
        self.changed = " "
        self.message = self.find_pattern = ""
        self.fname = None
        self.content = [""]
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
        self.undo_zero = 0
        self.case = "n"
        self.autoindent = "y"
        self.yank_buffer = []
        self.mark = None
    if sys.platform == "WiPy":
        def wr(self, s):
            sys.stdout.write(s)
        def not_pending(self):
            return True
        def rd(self):
            while True:
                try:
                    return sys.stdin.read(1).encode()
                except:
                    pass
    def goto(self, row, col):
        self.wr("\x1b[{};{}H".format(row + 1, col + 1))
    def clear_to_eol(self):
        self.wr(b"\x1b[0K")
    def cursor(self, onoff):
        self.wr(b"\x1b[?25h" if onoff else b"\x1b[?25l")
    def hilite(self, mode):
        if mode == 1: 
            self.wr(b"\x1b[1;47m")
        elif mode == 2: 
            self.wr(b"\x1b[43m")
        else: 
            self.wr(b"\x1b[0m")
    def set_screen_parms(self):
        self.cursor(False)
        self.wr('\x1b[999;999H\x1b[6n')
        pos = b''
        char = self.rd() 
        while char != b'R':
            pos += char
            char = self.rd()
        (self.height, self.width) = [int(i, 10) for i in pos[2:].split(b';')]
        self.height -= 1
        self.scrbuf = [(False,"\x00")] * self.height 
    def get_input(self): 
        while True:
            in_buffer = self.rd()
            if in_buffer == b'\x1b': 
                while True:
                    in_buffer += self.rd()
                    c = chr(in_buffer[-1])
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
            if in_buffer in self.KEYMAP:
                c = self.KEYMAP[in_buffer]
                if c != 0x1b:
                    return c
            elif len(in_buffer) == 1: 
                return in_buffer[0]
    def display_window(self): 
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
        self.col = max(0, min(self.col, len(self.content[self.cur_line])))
        if self.col >= self.width + self.margin:
            self.margin = self.col - self.width + (self.width >> 2)
        elif self.col < self.margin:
            self.margin = max(self.col - (self.width >> 2), 0)
        if not (self.top_line <= self.cur_line < self.top_line + self.height): 
            self.top_line = max(self.cur_line - self.row, 0)
        self.row = self.cur_line - self.top_line
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: 
                if self.scrbuf[c] != (False,''):
                    self.goto(c, 0)
                    self.clear_to_eol()
                    self.scrbuf[c] = (False,'')
            else:
                l = (self.mark != None and (
                    (self.mark <= i <= self.cur_line) or (self.cur_line <= i <= self.mark)),
                     self.content[i][self.margin:self.margin + self.width])
                if l != self.scrbuf[c]: 
                    self.goto(c, 0)
                    if l[0]: self.hilite(2)
                    self.wr(l[1])
                    if len(l[1]) < self.width:
                        self.clear_to_eol()
                    if l[0]: self.hilite(0)
                    self.scrbuf[c] = l
                i += 1
        self.goto(self.height, 0)
        self.hilite(1)
        self.wr("[{}] {} Row: {} Col: {}  {}".format(
            self.total_lines, self.changed, self.cur_line + 1,
            self.col + 1, self.message[:self.width - 25]))
        self.clear_to_eol() 
        self.hilite(0)
        self.goto(self.row, self.col - self.margin)
        self.cursor(True)
    def spaces(self, line, pos = None): 
        return (len(line) - len(line.lstrip(" ")) if pos == None else 
                len(line[:pos]) - len(line[:pos].rstrip(" ")))
    def line_range(self):
        return ((self.mark, self.cur_line + 1) if self.mark < self.cur_line else
                (self.cur_line, self.mark + 1))
    def line_edit(self, prompt, default): 
        self.goto(self.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        while True:
            key = self.get_input() 
            if key in (0x0a, 0x09): 
                self.hilite(0)
                return res
            elif key == 0x11: 
                self.hilite(0)
                return None
            elif key == 0x08: 
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == 0x7f: 
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: 
                if len(prompt) + len(res) < self.width - 2:
                    res += chr(key)
                    self.wr(chr(key))
    def find_in_file(self, pattern, pos, end):
        self.find_pattern = pattern 
        if self.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, end):
            if self.case != "y":
                match = self.content[line][spos:].lower().find(pattern)
            if match >= 0:
                break
            spos = 0
        else:
            self.message = "No match: " + pattern
            return 0
        self.col = match + spos
        self.cur_line = line
        return len(pattern)
    def handle_cursor_keys(self, key): 
        l = self.content[self.cur_line]
        if key == 0x0d:
                self.cur_line += 1
        elif key == 0x0b:
                self.cur_line -= 1
        elif key == 0x1f:
                self.col -= 1
        elif key == 0x1e:
                self.col += 1
        elif key == 0x10:
            self.col = self.spaces(l) if self.col == 0 else 0
        elif key == 0x03:
            self.col = len(l)
        elif key == 0x17:
            self.cur_line -= self.height
        elif key == 0x19:
            self.cur_line += self.height
        elif key == 0x06:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat, self.col, self.total_lines)
                self.row = self.height >> 1
        elif key == 0x0e:
            if self.find_pattern:
                self.find_in_file(self.find_pattern, self.col + 1, self.total_lines)
                self.row = self.height >> 1
        elif key == 0x07: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = self.height >> 1
                except:
                    pass
        elif key == 0x0c:
            self.mark = self.cur_line if self.mark == None else None
        else:
            return False
        return True
    def undo_add(self, lnum, text, key, span = 1):
        self.changed = '*'
        if self.undo_limit > 0 and (
           len(self.undo) == 0 or key == 0 or self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit: 
                del self.undo[0]
                self.undo_zero -= 1
            self.undo.append((lnum, span, text, key, self.col))
    def delete_lines(self, yank): 
        lrange = self.line_range()
        if yank:
            self.yank_buffer = self.content[lrange[0]:lrange[1]]
        self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], 0, 0) 
        del self.content[lrange[0]:lrange[1]]
        if self.content == []: 
            self.content = [""]
        self.total_lines = len(self.content)
        self.cur_line = lrange[0]
        self.mark = None 
    def handle_edit_key(self, key): 
        from os import rename, unlink
        l = self.content[self.cur_line]
        if key == 0x0a:
            self.mark = None
            self.undo_add(self.cur_line, [l], 0, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if self.autoindent == "y": 
                ni = min(self.spaces(l), self.col) 
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == 0x08:
            if self.mark != None:
                self.delete_lines(False)
            elif self.col > 0:
                self.undo_add(self.cur_line, [l], 0x08)
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
        elif key == 0x7f:
            if self.mark != None:
                self.delete_lines(False)
            elif self.col < len(l):
                self.undo_add(self.cur_line, [l], 0x7f)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines: 
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], 0)
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
        elif key == 0x09:
            if self.mark != None:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], 0xffff, lrange[1] - lrange[0]) 
                for i in range(lrange[0],lrange[1]):
                    if len(self.content[i]) > 0:
                        self.content[i] = ' ' * (self.tab_size - self.spaces(self.content[i]) % self.tab_size) + self.content[i]
            else:
                self.undo_add(self.cur_line, [l], 0x09)
                ni = self.tab_size - self.col % self.tab_size 
                self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
                self.col += ni
        elif key == 0x15:
            if self.mark != None:
                lrange = self.line_range()
                self.undo_add(lrange[0], self.content[lrange[0]:lrange[1]], 0xffff, lrange[1] - lrange[0]) 
                for i in range(lrange[0],lrange[1]):
                    ns = self.spaces(self.content[i])
                    if ns > 0:
                        self.content[i] = self.content[i][(ns - 1) % self.tab_size + 1:]
            else:
                ni = min((self.col - 1) % self.tab_size + 1, self.spaces(l, self.col)) 
                if ni > 0:
                    self.undo_add(self.cur_line, [l], 0x15)
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
        elif key == 0x18: 
            if self.mark != None:
                self.delete_lines(True)
        elif key == 0x04: 
            if self.mark != None:
                lrange = self.line_range()
                self.yank_buffer = self.content[lrange[0]:lrange[1]]
                self.mark = None
        elif key == 0x16: 
            if self.yank_buffer:
                if self.mark != None:
                    self.delete_lines(False)
                self.undo_add(self.cur_line, None, 0, -len(self.yank_buffer))
                self.content[self.cur_line:self.cur_line] = self.yank_buffer 
                self.total_lines += len(self.yank_buffer)
        elif key == 0x13:
            if True:
                    fname = self.fname
                    if fname == None:
                        fname = ""
                    fname = self.line_edit("Save File: ", fname)
                    lrange = (0, self.total_lines)
            if fname:
                try:
                    with open("tmpfile.pye", "w") as f:
                        for l in self.content[lrange[0]:lrange[1]]:
                                f.write(l + '\n')
                    try: unlink(fname)
                    except: pass
                    rename("tmpfile.pye", fname)
                    self.changed = ' ' 
                    self.undo_zero = len(self.undo) 
                    self.fname = fname 
                except Exception as err:
                    self.message = 'Could not save {}, {!r}'.format(fname, err)
        elif key == 0x1a:
            if len(self.undo) > 0:
                action = self.undo.pop(-1) 
                if action[3] != 0xffff:
                    self.cur_line = action[0]
                    self.col = action[4]
                if action[1] >= 0: 
                    if action[0] < self.total_lines:
                        self.content[action[0]:action[0] + action[1]] = action[2] 
                    else:
                        self.content += action[2]
                else: 
                    del self.content[action[0]:action[0] - action[1]]
                self.total_lines = len(self.content) 
                self.changed = ' ' if len(self.undo) == self.undo_zero else '*'
                self.mark = None
        elif key >= 0x20: 
            self.mark = None
            self.undo_add(self.cur_line, [l], 0x20 if key == 0x20 else 0x41)
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
    def edit_loop(self): 
        if self.content == []: 
            self.content = [""]
        self.total_lines = len(self.content)
        self.set_screen_parms()
        while True:
            if self.not_pending(): 
                self.display_window() 
            key = self.get_input() 
            self.message = '' 
            try:
                if key == 0x11:
                    if self.changed != ' ':
                        res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                        if not res or res[0].upper() != 'Y':
                            continue
                    self.goto(self.height, 0)
                    self.clear_to_eol()
                    return None
                elif key == 0x05:
                    self.set_screen_parms()
                    self.row = min(self.height - 1, self.row)
                    if sys.implementation.name == "micropython":
                        gc.collect()
                        self.message = "{} Bytes Memory available".format(gc.mem_free())
                elif self.handle_cursor_keys(key):
                    pass
                else: self.handle_edit_key(key)
            except Exception as err:
                self.message = "Internal error: {}".format(err)
    def get_file(self, fname):
        try:
                with open(fname) as f:
                    content = f.readlines()
        except Exception as err:
            message = 'Could not load {}, {!r}'.format(fname, err)
            return (None, message)
        for i in range(len(content)): 
            content[i] = expandtabs(content[i].rstrip('\r\n\t '))
        return (content, "")
def expandtabs(s):
    from _io import StringIO
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
        return sb.getvalue()
    else:
        return s
def pye(content = None, tab_size = 4, undo = 50, device = 0, baud = 115200):
    gc.collect() 
    e = Editor(tab_size, undo)
    if type(content) == str and content: 
        e.fname = content
        (e.content, e.message) = e.get_file(e.fname)
        if e.content == None: 
            print (e.message)
            return
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        e.content = content 
    e.edit_loop()
    return e.content if (e.fname == None) else e.fname
