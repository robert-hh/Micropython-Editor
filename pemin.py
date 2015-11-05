import sys, gc
class Editor:
    KEYMAP = { 
    b"\x1b[A" : 0x0b,
    b"\x1b[B" : 0x0d,
    b"\x1b[D" : 0x0c,
    b"\x1b[C" : 0x0f,
    b"\x1b[H" : 0x10, 
    b"\x1bOH" : 0x10, 
    b"\x1b[1~": 0x10, 
    b"\x1b[F" : 0x11, 
    b"\x1bOF" : 0x11, 
    b"\x1b[4~": 0x11, 
    b"\x1b[5~": 0x17,
    b"\x1b[6~": 0x19,
    b"\x11" : 0x03, 
    b"\r" : 0x0a,
    b"\x7f" : 0x08, 
    b"\x1b[3~": 0x1f,
    b"\x1b[Z" : 0x15, 
    b"\x1b[3;5~": 0x18, 
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
        self.message = ""
        self.find_pattern = ""
        self.fname = None
        self.content = [""]
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
        self.case = "n"
        self.autoindent = "y"
        self.yank_buffer = []
        self.lastkey = 0
    if sys.platform == "pyboard":
        @staticmethod
        def wr(s):
            ns = 0
            while ns < len(s): 
                res = Editor.serialcomm.write(s[ns:])
                if res != None:
                    ns += res
        @staticmethod
        def rd():
            while not Editor.serialcomm.any():
                pass
            return Editor.serialcomm.read(1)
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
    @staticmethod
    def scroll_region(stop):
        if stop:
            Editor.wr('\x1b[1;%dr' % stop) 
        else:
            Editor.wr('\x1b[r') 
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
        char = Editor.rd() 
        while char != b'R':
            if char in b"0123456789;": pos += char
            char = Editor.rd()
        (self.height, self.width) = [int(i, 10) for i in pos.split(b';')]
        self.height -= 1
        self.scrbuf = ["\x01"] * self.height 
        self.scroll_region(self.height)
    def get_input(self): 
        while True:
            in_buffer = Editor.rd()
            if in_buffer == b'\x1b': 
                while True:
                    in_buffer += Editor.rd()
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
                if self.scrbuf[c] != '':
                    self.goto(c, 0)
                    self.clear_to_eol()
                    self.scrbuf[c] = ''
            else:
                l = self.content[i][self.margin:self.margin + self.width]
                if l != self.scrbuf[c]: 
                    self.goto(c, 0)
                    self.wr(l)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = l
                i += 1
        self.goto(self.height, 0)
        self.hilite(1)
        self.wr("[%d] %c Row: %d Col: %d  %s" % (self.total_lines, self.changed, self.cur_line + 1, self.col + 1, self.message[:self.width - 25]))
        self.hilite(0)
        self.clear_to_eol() 
        self.goto(self.row, self.col - self.margin)
        self.cursor(True)
    def spaces(self, line, pos = None): 
        if pos == None: 
            return len(line) - len(line.lstrip(" "))
        else: 
            return len(line[:pos]) - len(line[:pos].rstrip(" "))
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
            elif key == 0x03: 
                self.hilite(0)
                return None
            elif key == 0x08: 
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == 0x1f: 
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: 
                if len(prompt) + len(res) < self.width - 2:
                    res += chr(key)
                    self.wr(chr(key))
    def find_in_file(self, pattern, pos):
        self.find_pattern = pattern 
        if self.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, self.total_lines):
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
    def cursor_down(self):
        if self.cur_line < self.total_lines - 1:
            self.cur_line += 1
            if self.cur_line == self.top_line + self.height:
                self.scroll_down(1)
    def handle_cursor_keys(self, key): 
        if key == 0x0d:
            self.cursor_down()
        elif key == 0x0b:
            if self.cur_line > 0:
                self.cur_line -= 1
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
        elif key == 0x0c:
                self.col -= 1
        elif key == 0x0f:
                self.col += 1
        elif key == 0x10:
            self.col = self.spaces(self.content[self.cur_line]) if self.col == 0 else 0
        elif key == 0x11:
            self.col = len(self.content[self.cur_line])
        elif key == 0x17:
            self.cur_line -= self.height
        elif key == 0x19:
            self.cur_line += self.height
        elif key == 0x06:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat, self.col)
                self.row = self.height >> 1
        elif key == 0x0e:
            if self.find_pattern:
                self.find_in_file(self.find_pattern, self.col + 1)
                self.row = self.height >> 1
        elif key == 0x07: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = self.height >> 1
                except:
                    pass
        else:
            return False
        return True
    def undo_add(self, lnum, text, key, span = 1):
        self.changed = '*'
        if self.undo_limit > 0 and (
           len(self.undo) == 0 or key == 0 or self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit: 
                del self.undo[0]
                self.sticky_c = "*"
            self.undo.append((lnum, span, text, key, self.col))
    def handle_edit_key(self, key): 
        l = self.content[self.cur_line]
        if key == 0x0a:
            self.undo_add(self.cur_line, [l], 0, 2)
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if self.autoindent == "y": 
                ni = min(self.spaces(l), self.col) 
                r = l.partition("\x23")[0].rstrip() 
                if r and r[-1] == ':' and self.col >= len(r): 
                    ni += self.tab_size
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == 0x08:
            if self.col > 0:
                self.undo_add(self.cur_line, [l], key)
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
        elif key == 0x1f:
            if self.col < len(l):
                self.undo_add(self.cur_line, [l], key)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines: 
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], 0)
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
        elif key == 0x09:
                self.undo_add(self.cur_line, [l], key)
                ni = self.tab_size - self.col % self.tab_size 
                self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
                self.col += ni
        elif key == 0x15:
                ni = min((self.col - 1) % self.tab_size + 1, self.spaces(l, self.col)) 
                if ni > 0:
                    self.undo_add(self.cur_line, [l], key)
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
        elif key == 0x18: 
            if key == self.lastkey: 
                self.yank_buffer.append(l) 
            else:
                self.yank_buffer = [l]
            if self.total_lines > 1: 
                self.undo_add(self.cur_line, [l], 0, 0) 
                del self.content[self.cur_line]
                self.total_lines -= 1
            else: 
                self.undo_add(self.cur_line, [l], 0, 1) 
                self.content[self.cur_line] = ''
        elif key == 0x04: 
            if key == self.lastkey: 
                self.yank_buffer.append(l) 
            else:
                self.yank_buffer = [l]
            self.cursor_down()
        elif key == 0x16: 
            if self.yank_buffer:
                self.undo_add(self.cur_line, None, 0, -len(self.yank_buffer))
                self.content[self.cur_line:self.cur_line] = self.yank_buffer 
                self.total_lines += len(self.yank_buffer)
        elif key == 0x13:
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
                    self.sticky_c = " " 
                    del self.undo[:]
                    self.fname = fname 
                except Exception as err:
                    self.message = 'Could not save %s, Error: %s' % (fname, err)
        elif key == 0x1a:
            if len(self.undo) > 0:
                action = self.undo.pop(-1) 
                self.cur_line = action[0]
                self.col = action[4]
                if action[1] >= 0: 
                    if action[0] < self.total_lines:
                        self.content[self.cur_line:self.cur_line + action[1]] = action[2] 
                    else:
                        self.content += action[2]
                else: 
                    del self.content[self.cur_line : self.cur_line - action[1]]
                self.total_lines = len(self.content) 
                if len(self.undo) == 0: 
                    self.changed = self.sticky_c
        elif key >= 0x20: 
            self.undo_add(self.cur_line, [l], 0x20 if key == 0x20 else 0x41)
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
    def edit_loop(self): 
        if len(self.content) == 0: 
            self.content = [""]
        self.total_lines = len(self.content)
        self.set_screen_parms()
        while True:
            self.display_window() 
            key = self.get_input() 
            self.message = '' 
            try:
                if key == 0x03:
                    if self.changed != ' ':
                        res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                        if not res or res[0].upper() != 'Y':
                            continue
                    self.scroll_region(0)
                    self.goto(self.height, 0)
                    self.clear_to_eol()
                    return None
                elif key == 0x05:
                    self.set_screen_parms()
                    self.row = min(self.height - 1, self.row)
                    if sys.implementation.name == "micropython":
                        gc.collect()
                        self.message = "%d Bytes Memory available" % gc.mem_free()
                elif self.handle_cursor_keys(key):
                    pass
                else: self.handle_edit_key(key)
                self.lastkey = key
            except MemoryError:
                del self.undo[:]
                del self.yank_buffer[:]
                gc.collect()
                self.message = "Memory Error. Undo and Yank cleared!"
    def expandtabs(self, s):
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
    def get_file(self, fname):
        from os import listdir
        if fname in listdir():
                with open(fname) as f:
                    content = f.readlines()
        else:
            message = 'Could not load %s, File is not in the local directory' % fname
            return (None, message)
        for i in range(len(content)): 
            content[i] = self.expandtabs(content[i].rstrip('\r\n\t '))
        return (content, "")
def pye(content = None, tab_size = 4, undo = 50, device = 0, baud = 115200):
    e = Editor(tab_size, undo)
    if type(content) == str and content: 
        e.fname = content
        (e.content, e.message) = e.get_file(e.fname)
        if e.content == None: 
            print (e.message)
            return
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        
        e.content = content
    e.init_tty(device, baud)
    e.edit_loop()
    e.deinit_tty()
    return e.content if (e.fname == None) else e.fname
