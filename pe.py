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
    b"\x04" : 0x4020, 
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
    def get_input(self): 
        if len(self.k_buffer) == 0:
            self.k_buffer = Editor.rd() 
        while True:
            for k in self.KEYMAP.keys():
                if k.startswith(self.k_buffer): 
                    if self.k_buffer == k:
                        c = self.KEYMAP[self.k_buffer]
                        self.k_buffer = b""
                        return c 
                    else: 
                        break
            else: 
                c = self.k_buffer[0]
                if c >= ord(' '): 
                    self.k_buffer = self.k_buffer[1:]
                    return c
                else: 
                    if c == ord('\x1b'): 
                        c = chr(self.k_buffer[-1])
                        self.k_buffer = b""
                        while c != '~' and not c.isalpha():
                            c = Editor.rd().decode()
                    else: 
                        self.k_buffer = self.k_buffer[1:]
            self.k_buffer += Editor.rd() 
    def display_window(self):
        self.col = min(self.col, len(self.content[self.cur_line]))
        if self.col >= self.width + self.margin:
            self.margin = self.col - self.width + int(self.width / 4)
        elif self.col < self.margin:
            self.margin = max(self.col - int(self.width / 4), 0)
        if self.top_line <= self.cur_line < self.top_line + self.height: 
            self.row = self.cur_line - self.top_line
        else: 
            self.top_line = self.cur_line - self.row
            if self.top_line < 0:
                self.top_line = 0
                self.row = self.cur_line
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            self.goto(c, 0)
            if i == self.total_lines:
                self.clear_to_eol()
                self.scrbuf[c] = ""
            else:
                l = self.content[i]
                match = ("def " in l or "class " in l) and ':' in l
                l = l[self.margin:self.margin + self.width]
                if l != self.scrbuf[c]: 
                    if match: self.hilite(True)
                    self.wr(l)
                    if match: self.hilite(False)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = l
                i += 1
        if self.status or self.message:
            self.goto(self.height, 0)
            self.hilite(True)
            self.wr("%c Ln: %d Col: %d  %s" % (self.changed, self.cur_line + 1, self.col + 1, self.message))
            self.clear_to_eol()
            self.hilite(False)
        self.cursor(True)
        self.goto(self.row, self.col - self.margin)
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
            key = self.get_input() 
            if key in (0x400a, 0x400e): 
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
    def find_in_file(self, pattern, pos, case = False):
        self.find_pattern = pattern 
        spos = pos
        for line in range(self.cur_line, self.total_lines):
            if case:
                match = self.content[line][spos:].find(pattern)
            else:
                match = self.content[line][spos:].lower().find(pattern)
            if match >= 0:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return False
        self.col = match + spos
        self.cur_line = line
        return True
    def handle_cursor_keys(self, key): 
        if key == 0x4002:
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
        elif key == 0x4001:
            if self.cur_line > 0:
                self.cur_line -= 1
        elif key == 0x4003:
            if (self.col > 0):
                self.col -= 1
        elif key == 0x4004:
            self.col += 1
        elif key == 0x4005:
            ns = self.spaces(self.content[self.cur_line])
            if self.col > ns:
                self.col = ns
            else:
                self.col = 0
        elif key == 0x4006:
            self.col = len(self.content[self.cur_line])
        elif key == 0x4007:
            self.cur_line -= self.height
            if self.cur_line < 0:
                self.cur_line = 0
        elif key == 0x4008:
            self.cur_line += self.height
            if self.cur_line >= self.total_lines:
                self.cur_line = self.total_lines - 1
        elif key == 0x4010:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat.lower(), self.col, False)
        elif key == 0x4014:
            if self.find_in_file(self.find_pattern, self.col + 1, False):
                self.message = ' ' 
        elif key == 0x4011: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    target = int(line)
                    self.cur_line = min(self.total_lines - 1, max(target - 1, 0))
                except:
                    pass
        elif key == 0x4012: 
            self.cur_line = 0
        elif key == 0x4013: 
            self.cur_line = self.total_lines - 1
            self.message = ' ' 
        elif key == 0x4018: 
            self.autoindent = not self.autoindent
            self.message = "Autoindent %s" % self.autoindent
        else:
            return False
        return True
    def handle_key(self, key): 
        l = self.content[self.cur_line]
        sc = self.changed
        self.changed = '*'
        if key == 0x400a:
            self.content[self.cur_line] = l[:self.col]
            if self.autoindent:
                ni = min(self.spaces(l, 0), self.col) 
                r = self.content[self.cur_line].partition("\x23")[0].rstrip() 
                if r and r[-1] == ':' and self.col >= len(r): 
                    ni += self.tab_size
            else:
                ni = 0
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == 0x400b:
            if self.col:
                self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
            elif self.cur_line: 
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += l
                del self.content[self.cur_line]
                self.cur_line -= 1
                self.total_lines -= 1
            else:
                self.changed = sc
        elif key == 0x400c:
            if self.col < len(l):
                l = l[:self.col] + l[self.col + 1:]
                self.content[self.cur_line] = l
            elif (self.cur_line + 1) < self.total_lines: 
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)
                self.total_lines -= 1
            else:
                self.changed = sc
        elif key == 0x400e: 
            ns = self.spaces(l, 0)
            if ns and self.col < ns: 
                ni = self.tab_size - ns % self.tab_size
            else:
                ni = self.tab_size - self.col % self.tab_size
            self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
            if ns == len(l) or self.col >= ns: 
                self.col += ni 
        elif key == 0x400f: 
            ns = self.spaces(l, 0)
            if ns and self.col < ns: 
                ni = (ns - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[ni:]
            else: 
                ns = self.spaces(l, self.col)
                ni = (self.col - 1) % self.tab_size + 1
                if (ns >= ni):
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
                else:
                    self.changed = sc
        elif key == 0x4015: 
            if key == self.lastkey: 
                self.y_buffer.append(l) 
            else:
                del self.y_buffer 
                self.y_buffer = [l]
            if self.total_lines > 1: 
                del self.content[self.cur_line]
                self.total_lines -= 1
                if self.cur_line >= self.total_lines: 
                    self.cur_line -= 1
            else: 
                self.content[self.cur_line] = ''
        elif key == 0x4020: 
            if key == self.lastkey: 
                self.y_buffer.append(l) 
            else:
                del self.y_buffer 
                self.y_buffer = [l]
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
            self.changed = sc
        elif key == 0x4017: 
            if self.y_buffer:
                self.content[self.cur_line:self.cur_line] = self.y_buffer 
                self.total_lines += len(self.y_buffer)
            else:
                self.changed = sc
        elif key == 0x4019:
            count = 0
            found = False
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("Replace with: ", self.replc_pattern)
                if rpat != None:
                    self.replc_pattern = rpat
                    q = ''
                    while True:
                        if self.find_in_file(pat, self.col, True):
                            found = True
                            if q != 'a':
                                self.display_window()
                                self.goto(self.height, 0)
                                self.wr("Replace (yes/No/all/quit) ? ")
                                self.goto(self.row, self.col - self.margin)
                                key = self.get_input() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x4009:
                                break
                            elif q in ('a','y'):
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + len(pat):]
                                self.col += len(rpat)
                                count += 1
                            else: 
                                self.col += 1
                        else:
                            break
                    if found:
                        self.message = "Replaced %d times" % count
            if count == 0:
                self.changed = sc
        elif 32 <= key < 0x4000:
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
        else: 
            self.changed = sc
    def loop(self): 
        while True:
            self.display_window() 
            key = self.get_input() 
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
    def set_lines(self, lines, fname):
        self.content = lines
        self.total_lines = len(lines)
        self.fname = fname
        self.cls()
        self.scrbuf = [""] * self.height
    def init_tty(self, device, baud):
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
            Editor.sdev = device
        
        self.wr(b'\x1b[2J\x1b7\x1b[r\x1b[999;999H\x1b[6n')
        pos = b''
        while True:
            char = self.rd()
            if char == b'R':
                break
            if char != b'\x1b' and char != b'[':
                pos += char
        (height, width) = [int(i, 10) for i in pos.split(b';')]
        self.height = height - 1
        self.width = width
    def deinit_tty(self):
        
        self.goto(self.height, 0)
        self.clear_to_eol()
        if sys.platform == "pyboard" and not Editor.sdev:
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
        return r + s[last:]
    else:
        return s
def pye(name = "", content = [" "], tab_size = 4, status = True, device = 0, baud = 38400):
    if name:
        try:
            with open(name) as f:
                content = [expandtabs(l.rstrip('\r\n\t ')) for l in f]
        except Exception as err:
            print("Could not load %s, Reason %s" % (name, err))
            return
    elif not content:
        content = [" "]
    e = Editor(tab_size, status)
    e.init_tty(device, baud)
    e.set_lines(content, name)
    e.loop()
    e.deinit_tty()
 
    del e
    if name:
        content.clear()
    if sys.platform == "pyboard":
        import gc
        gc.collect()
