import sys
if sys.platform == "pyboard":
    import pyb
class Editor:
    KEYMAP = { 
    b"\x1b[A" : 0x4001,
    b"\x1b[B" : 0x4002,
    b"\x1b[D" : 0x4003,
    b"\x1b[C" : 0x4004,
    b"\x0b" : 0x4001, 
    b"\x0a" : 0x4002, 
    b"\x08" : 0x4003, 
    b"\x0c" : 0x4004,
    b"\x1b[H" : 0x4005, 
    b"\x1bOH" : 0x4005, 
    b"\x1b[1~": 0x4005, 
    b"\x17" : 0x4005, 
    b"\x1b[F" : 0x4006, 
    b"\x1bOF" : 0x4006, 
    b"\x1b[4~": 0x4006, 
    b"\x05" : 0x4006, 
    b"\x1b[5~": 0x4007,
    b"\x0f" : 0x4007, 
    b"\x1b[6~": 0x4008,
    b"\x10" : 0x4008, 
    b"\x11" : 0x4009, 
    b"\x03" : 0x4009, 
    b"\r" : 0x400a,
    b"\x7f" : 0x400b, 
    b"\x1b[3~": 0x400c,
    b"\x19" : 0x400c, 
    b"\x13" : 0x400d, 
    b"\x06" : 0x4010, 
    b"\x0e" : 0x4014, 
    b"\x07" : 0x4011, 
    b"\x14" : 0x4012, 
    b"\x1b[1;5H": 0x4012,
    b"\x02" : 0x4013, 
    b"\x1b[1;5F": 0x4013,
    b"\x1b[3;5~": 0x4015,
    b"\x18" : 0x4015, 
    b"\x09" : 0x400e,
    b"\x1b[Z" : 0x400f, 
    b"\x15" : 0x400f, 
    b"\x16" : 0x4017, 
    b"\x01" : 0x4018, 
    b"\x12" : 0x4019, 
    }
    def __init__(self, tab_size, status):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.margin = 0
        self.k_buffer = b""
        self.tab_size = tab_size
        self.status = status
        self.autoindent = True
        self.changed = ' '
        self.message = ""
        self.find_pattern = ""
        self.replc_pattern = ""
        self.y_buffer = []
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
    def cls():
        Editor.wr(b"\x1b[2J")
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
    def hilite(onoff):
        if onoff:
            Editor.wr(b"\x1b[1m")
        else:
            Editor.wr(b"\x1b[0m")
    def c_or_f(self): 
        if len(self.k_buffer) == 0:
            self.k_buffer += Editor.rd() 
        while True:
            for k in self.KEYMAP.keys():
                if self.k_buffer == k[:len(self.k_buffer)]: 
                    if self.k_buffer == k:
                        c = self.KEYMAP[self.k_buffer]
                        self.k_buffer = b""
                        return c 
                    else: 
                        break
            else: 
                c = self.k_buffer[0]
                self.k_buffer = self.k_buffer[1:]
                return c
            self.k_buffer += Editor.rd() 
    def adjust_cursor_eol(self):
        self.col = min(self.col, len(self.content[self.cur_line]) - self.margin)
        if not (0 <= self.col < self.width): 
            return self.adjust_col(True)
    def adjust_col(self, updt):
        
            if self.col >= self.width:
                self.margin = self.col + self.margin - (self.width - 1) + self.hstep
                self.col = self.width - 1 - self.hstep
                self.update_screen()
                return True
            elif self.col < 0:
                val = self.col + self.margin 
                self.margin = max(self.margin - self.width, 0)
                self.col = val - self.margin
                self.update_screen()
                return True
            else:
                if updt: self.update_line()
                return False
    def adjust_row(self):
        
        if self.top_line <= self.cur_line < self.top_line + self.height: 
            self.row = self.cur_line - self.top_line
            return self.adjust_cursor_eol() 
        else:
            self.top_line = self.cur_line - self.row
            if self.top_line < 0:
                self.top_line = 0
                self.row = self.cur_line
            if not self.adjust_cursor_eol(): 
                self.update_screen()
            return True
    def set_lines(self, lines, fname):
        self.content = lines
        self.total_lines = len(lines)
        self.fname = fname
    def update_screen(self):
        self.cursor(False)
        self.cls()
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            self.goto(c, 0)
            if i == self.total_lines:
                self.clear_to_eol()
            else:
                self.show_line(self.content[i])
                i += 1
        self.cursor(True)
    def update_line(self):
        self.cursor(False)
        self.goto(self.row, 0)
        self.show_line(self.content[self.cur_line])
        self.cursor(True)
    def show_line(self, l):
        l = l[self.margin:]
        l = l[:self.width]
        self.wr(l)
        if len(l) < self.width: self.clear_to_eol()
    def show_status(self):
        if self.status or self.message:
            self.cursor(False)
            self.goto(self.height, 0)
            self.hilite(True)
            self.wr("%c Ln: %d Col: %d  %s" %
                    (self.changed, self.cur_line + 1, self.col + self.margin + 1, self.message))
            self.clear_to_eol()
            self.hilite(False)
            self.cursor(True)
    def clear_status(self):
        if (not self.status) and self.message:
            self.goto(self.height, 0)
            self.clear_to_eol()
        self.message = ''
    def spaces(self, line, pos = 0): 
        if pos: 
            return len(line[:pos]) - len(line[:pos].rstrip(" "))
        else: 
            return len(line) - len(line.lstrip(" "))
    def line_edit(self, prompt, default): 
        self.goto(self.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' 
        while True:
            key = self.c_or_f() 
            if key == 0x400a: 
                self.hilite(False)
                return res
            elif key == 0x4009: 
                self.hilite(False)
                return None
            elif key in (0x400b, 0x400c): 
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif 0x20 <= key < 0x100: 
                res += chr(key)
                self.wr(chr(key))
            else: 
                pass
    def find_in_file(self, pattern, pos):
        self.find_pattern = pattern 
        spos = pos + self.margin
        for line in range(self.cur_line, self.total_lines):
            match = self.content[line][spos:].lower().find(pattern)
            if match >= 0:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return False
        self.col = match - self.margin
        self.cur_line = line
        self.adjust_col(False)
        self.adjust_row()
        return True
    def handle_cursor_keys(self, key): 
        if key == 0x4002:
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
                self.adjust_row()
        elif key == 0x4001:
            if self.cur_line > 0:
                self.cur_line -= 1
                self.adjust_row()
        elif key == 0x4003:
            self.col -= 1
            self.adjust_col(False)
        elif key == 0x4004:
            self.col += 1
            self.adjust_cursor_eol()
        elif key == 0x4005:
            ns = self.spaces(self.content[self.cur_line])
            if self.col + self.margin > ns:
                self.col = ns - self.margin
            else:
                self.col = -self.margin
            self.adjust_col(False)
        elif key == 0x4006:
            self.col = len(self.content[self.cur_line]) - self.margin
            self.adjust_col(False)
        elif key == 0x4007:
            self.cur_line -= self.height
            if self.cur_line < 0:
                self.cur_line = 0
            self.adjust_row()
        elif key == 0x4008:
            self.cur_line += self.height
            if self.cur_line >= self.total_lines:
                self.cur_line = self.total_lines - 1
            self.adjust_row()
        elif key == 0x4010:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat.lower(), self.col)
        elif key == 0x4014:
            self.find_in_file(self.find_pattern, self.col + 1)
            self.message = ' ' 
        elif key == 0x4011: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                self.cur_line = min(self.total_lines - 1, max(int(line) - 1, 0))
                self.adjust_row()
        elif key == 0x4012: 
            self.cur_line = 0
            self.adjust_row()
        elif key == 0x4013: 
            self.cur_line = self.total_lines - 1
            self.adjust_row()
            self.message = ' ' 
        elif key == 0x4018: 
            self.autoindent = not self.autoindent
            self.message = "Autoindent %s" % self.autoindent
        else:
            return False
        return True
    def handle_buffer_keys(self, key): 
            if key == 0x400d:
                fname = self.line_edit("File Name: ", self.fname)
                if fname:
                    try:
                        with open(fname, "w") as f:
                            self.wr(" ..Saving..")
                            for l in self.content:
                                f.write(l + '\n')
                        self.changed = " "
                    except:
                        pass
            else:
                return False
            return True
    def handle_key(self, key): 
        l = self.content[self.cur_line]
        sc = self.changed
        self.changed = '*'
        if key == 0x400a:
            self.content[self.cur_line] = l[:self.col + self.margin]
            if self.autoindent and self.col + self.margin > 0:
                ni = self.spaces(l, 0)
            else:
                ni = 0
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col + self.margin:]]
            self.total_lines += 1
            self.col = ni - self.margin
            if not self.adjust_row(): 
                self.update_screen() 
        elif key == 0x400b:
            if self.col + self.margin:
                self.content[self.cur_line] = l[:self.col + self.margin - 1] + l[self.col + self.margin:]
                self.col -= 1
                self.adjust_col(True)
            elif self.cur_line: 
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += l
                del self.content[self.cur_line]
                self.cur_line -= 1
                self.total_lines -= 1
                self.adjust_col(False)
                if not self.adjust_row(): 
                    self.update_screen() 
            else:
                self.changed = sc
        elif key == 0x400c:
            if (self.col + self.margin) < len(l):
                l = l[:self.col + self.margin] + l[self.col + self.margin + 1:]
                self.content[self.cur_line] = l
                self.update_line()
            elif (self.cur_line + 1) < self.total_lines: 
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
                self.update_screen()
            else:
                self.changed = sc
        elif key == 0x4015: 
            if key == self.lastkey: 
                self.y_buffer.append(l) 
            else:
                del self.y_buffer 
                self.y_buffer = [l]
            self.y_mode = True
            if self.total_lines > 1: 
                del self.content[self.cur_line]
                self.total_lines -= 1
                if self.cur_line >= self.total_lines: 
                    self.cur_line -= 1
            else: 
                self.content[self.cur_line] = ''
            if not self.adjust_row(): 
                self.update_screen() 
        elif key == 0x400e: 
            ns = self.spaces(l, 0)
            ni = self.tab_size - ns % self.tab_size
            self.content[self.cur_line] = l[:self.col + self.margin] + ' ' * ni + l[self.col + self.margin:]
            if ns == len(l) or self.col + self.margin >= ns: 
                self.col += ni 
            self.adjust_col(True)
        elif key == 0x400f: 
            ns = self.spaces(l, 0)
            if ns and self.col + self.margin < ns: 
                ni = (ns - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[ni:]
                self.adjust_col(True)
            else: 
                ns = self.spaces(l, self.col + self.margin)
                ni = (self.col + self.margin - 1) % self.tab_size + 1
                if (ns >= ni):
                    self.content[self.cur_line] = l[:self.col + self.margin - ni] + l[self.col + self.margin:]
                    self.col -= ni
                    self.adjust_col(True)
                else:
                    self.changed = sc
        elif key == 0x4017: 
            if self.y_buffer:
                self.content[self.cur_line:self.cur_line] = self.y_buffer 
                self.total_lines += len(self.y_buffer)
                if not self.adjust_cursor_eol(): 
                    self.update_screen() 
            else:
                self.changed = sc
        elif key == 0x4019:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("Replace with: ", self.replc_pattern)
                if rpat != None:
                    self.replc_pattern = rpat
                    count = 0
                    q = ''
                    while True:
                        if self.find_in_file(pat.lower(), self.col):
                            if q != 'a':
                                self.update_screen() 
                                self.goto(self.height, 0)
                                self.wr("Replace (yes/No/all/quit) ? ")
                                self.goto(self.row, self.col)
                                key = self.c_or_f() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x4009:
                                break
                            elif q in ('a','y'):
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col + self.margin] + rpat + self.content[self.cur_line][self.col + self.margin + len(pat):]
                                self.col += len(rpat)
                                count += 1
                            else: 
                                self.col += len(pat)
                        else:
                            break
                    self.update_screen() 
                    self.message = "Replaced %d times" % count
                else:
                    self.changed = sc
            else:
                self.changed = sc
        elif 32 <= key < 0x4000:
            self.content[self.cur_line] = l[:self.col + self.margin] + chr(key) + l[self.col + self.margin:]
            self.col += 1
            self.adjust_col(True)
        else: 
            self.changed = sc
    def loop(self): 
        self.update_screen()
        while True:
            self.show_status()
            self.goto(self.row, self.col) 
            key = self.c_or_f() 
            self.clear_status()
            if key == 0x4009:
                if self.changed != ' ':
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                return None
            elif key == 0x400d:
                fname = self.line_edit("File Name: ", self.fname)
                if fname:
                    try:
                        with open(fname, "w") as f:
                            self.wr(" ..Saving..")
                            for l in self.content:
                                f.write(l + '\n')
                        self.changed = " "
                    except:
                        pass
            elif self.handle_cursor_keys(key):
                pass
            else: self.handle_key(key)
            self.lastkey = key
    def init_tty(self, device, baud):
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
            Editor.sdev = device
        
        self.wr(b'\x1b7\x1b[r\x1b[999;999H\x1b[6n')
        pos = b''
        while True:
            char = self.rd()
            if char == b'R':
                break
            if char != b'\x1b' and char != b'[':
                pos += char
        self.wr(b'\x1b8')
        (height, width) = [int(i, 10) for i in pos.split(b';')]
        self.height = height - 1
        self.width = width
        self.hstep = int(width / 6)
    def deinit_tty(self):
        
        self.goto(self.height, 0)
        self.clear_to_eol()
        if sys.platform == "pyboard":
            Editor.serialcomm.setinterrupt(3)
def expandtabs(s):
    if '\t' in s:
        r, last, i = ("", 0, 0) 
        while i < len(s):
            if s[i] == '\t': 
                r += s[last:i]
                r += " " * ( 8 - len(r) % 8)
                last = i + 1
            i += 1
        return r + s[last:i+1]
    else:
        return s
def pye(name="", content=[""], tab_size=4, status=True, device=0, baud=38400):
    if name:
       try:
            with open(name) as f:
                content = [expandtabs(l.rstrip('\r\n\t')) for l in f]
       except Exception as err:
            print("Could not load %s, Reason %s" % (name, err))
            return
    else:
        content = ["", ""]
    e = Editor(tab_size, status)
    e.init_tty(device, baud)
    e.set_lines(content, name)
    e.loop()
    e.deinit_tty()
 
    if name:
        content.clear()
    if sys.platform == "pyboard":
        import gc
        gc.collect()
