import sys
import gc
import _io
if sys.platform == "pyboard":
    import pyb
class Editor:
    KEYMAP = { 
    b"\x1b[A" : 0x4001,
    b"\x1b[B" : 0x4002,
    b"\x1b[D" : 0x4003,
    b"\x1b[C" : 0x4004,
    b"\x1b[H" : 0x4005, 
    b"\x1bOH" : 0x4005, 
    b"\x1b[1~": 0x4005, 
    b"\x1b[F" : 0x4006, 
    b"\x1bOF" : 0x4006, 
    b"\x1b[4~": 0x4006, 
    b"\x1b[5~": 0x4007,
    b"\x1b[6~": 0x4008,
    b"\x11" : 0x4009, 
    b"\x03" : 0x4009, 
    b"\r" : 0x400a,
    b"\n" : 0x400a,
    b"\x7f" : 0x400b, 
    b"\x08" : 0x400b,
    b"\x1b[3~": 0x400c,
    b"\x13" : 0x400d, 
    b"\x06" : 0x4010, 
    b"\x0e" : 0x4014, 
    b"\x07" : 0x4011, 
    b"\x1b[M" : 0x401b,
    b"\x01" : 0x4018, 
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
    b"\x12" : 0x4019, 
    b"\x04" : 0x401a, 
    }
    def __init__(self, tab_size):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.margin = 0
        self.k_buffer = b""
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
                        if c == 0x401b: 
                            mf = ord((Editor.rd())) & 0xe3 
                            self.mouse_x = ord(Editor.rd()) - 33
                            self.mouse_y = ord(Editor.rd()) - 33
                            if mf == 0x61:
                                return 0x401d
                            elif mf == 0x60:
                                return 0x401c
                            else:
                                return 0x401b 
                        else:
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
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
        self.col = max(0, min(self.col, len(self.content[self.cur_line])))
        if self.col >= self.width + self.margin:
            self.margin = self.col - self.width + int(self.width / 4)
        elif self.col < self.margin:
            self.margin = max(self.col - int(self.width / 4), 0)
        if not (self.top_line <= self.cur_line < self.top_line + self.height): 
            self.top_line = max(self.cur_line - self.row, 0)
        self.row = self.cur_line - self.top_line
        self.cursor(False)
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: 
                if self.scrbuf[c]:
                    self.goto(c, 0)
                    self.clear_to_eol()
                    self.scrbuf[c] = ""
            else:
                l = self.content[i]
                match = ("def " in l or "class " in l) and '\x3a' in l
                l = l[self.margin:self.margin + self.width]
                if l != self.scrbuf[c]: 
                    self.goto(c, 0)
                    if match: self.hilite(True)
                    self.wr(l)
                    if match: self.hilite(False)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = l
                i += 1
        if self.status == "y" or self.message:
            self.goto(self.height, 0)
            self.hilite(True)
            self.wr("%c Ln: %d Col: %d  %s" % (self.changed, self.cur_line + 1, self.col + 1, self.message))
            self.clear_to_eol()
            self.hilite(False)
        self.cursor(True)
        self.goto(self.row, self.col - self.margin)
    def clear_status(self):
        if (self.status != "y") and self.message:
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
                if len(prompt) + len(res) < self.width - 1:
                    res += chr(key)
                    self.wr(chr(key))
            else: 
                pass
    def find_in_file(self, pattern, pos):
        self.find_pattern = pattern 
        if self.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, self.total_lines):
            if self.case == "y":
                match = self.content[line][spos:].find(pattern)
            else:
                match = self.content[line][spos:].lower().find(pattern)
            if match >= 0:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return 0
        self.col = match + spos
        self.cur_line = line
        self.message = ' ' 
        return len(pattern)
    def handle_cursor_keys(self, key): 
        if key == 0x4002:
            self.cur_line += 1
        elif key == 0x4001:
            self.cur_line -= 1
        elif key == 0x4003:
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
        elif key == 0x4008:
            self.cur_line += self.height
        elif key == 0x4010:
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                self.find_in_file(pat, self.col)
                self.row = int(self.height / 2)
        elif key == 0x4014:
            if self.find_pattern:
                self.find_in_file(self.find_pattern, self.col + 1)
                self.row = int(self.height / 2)
        elif key == 0x4011: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = int(self.height / 2)
                except:
                    pass
        elif key == 0x401b: 
            if self.mouse_y < self.height:
                self.col = self.mouse_x + self.margin
                self.cur_line = self.mouse_y + self.top_line
        elif key == 0x401c: 
            self.top_line = max(self.top_line - 3, 0)
            self.cur_line = min(self.cur_line, self.top_line + self.height - 1)
        elif key == 0x401d: 
            self.top_line = min(self.top_line + 3, self.total_lines - 1)
            self.cur_line = max(self.cur_line, self.top_line)
        elif key == 0x4018: 
            pat = self.line_edit("Case Sensitive %c, Statusline %c, Autoindent %c: " % (self.case, self.status, self.autoindent), "")
            try:
                res = [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case = res[0][0]
                if res[1]: self.status = res[1][0]
                if res[2]: self.autoindent = res[2][0]
            except:
                pass
        elif key == 0x4012: 
            self.cur_line = 0
        elif key == 0x4013: 
            self.cur_line = self.total_lines - 1
            self.row = int(self.height / 2)
            self.message = ' ' 
        else:
            return False
        return True
    def handle_edit_key(self, key): 
        l = self.content[self.cur_line]
        sc = self.changed
        self.changed = '*'
        if key == 0x400a:
            self.content[self.cur_line] = l[:self.col]
            ni = 0
            if self.autoindent == "y": 
                ni = min(self.spaces(l, 0), self.col) 
                r = self.content[self.cur_line].partition("\x23")[0].rstrip() 
                if r and r[-1] == ':' and self.col >= len(r): 
                    ni += self.tab_size
            self.cur_line += 1
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]]
            self.total_lines += 1
            self.col = ni
        elif key == 0x400b:
            if self.col > 0:
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
                ni = 0
                if self.autoindent == "y": 
                    ni = self.spaces(self.content[self.cur_line + 1])
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)[ni:]
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
        elif key == 0x401a: 
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
            self.changed = sc
            pat = self.line_edit("Find: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("Replace with: ", self.replc_pattern)
                if rpat != None:
                    self.replc_pattern = rpat
                    q = ''
                    while True:
                        ni = self.find_in_file(pat, self.col)
                        if ni:
                            found = True
                            if q != 'a':
                                self.message = "Replace (yes/No/all/quit) ? "
                                self.display_window()
                                key = self.get_input() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x4009:
                                break
                            elif q in ('a','y'):
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                            else: 
                                self.col += 1
                        else:
                            break
                    if found:
                        self.message = "Replaced %d times" % count
            if count > 0:
                self.changed = '*'
        elif key == 0x400d:
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
            else:
                self.changed = sc
        elif 32 <= key < 0x4000:
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
        else: 
            self.changed = sc
    def edit_loop(self): 
        self.scrbuf = [""] * self.height
        self.cls()
        self.total_lines = len(self.content)
        
        for i in range(self.total_lines):
            if sys.implementation.name == 'micropython':
                self.content[i] = self.expandtabs(self.content[i].rstrip('\r\n\t '))
        while True:
            self.display_window() 
            key = self.get_input() 
            self.clear_status() 
            if key == 0x4009:
                if self.changed != ' ' and self.fname != None:
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                return None
            elif self.handle_cursor_keys(key):
                pass
            else: self.handle_edit_key(key)
            self.lastkey = key
    def init_tty(self, device, baud):
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
                self.status = "n"
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
                self.status = "y"
            Editor.sdev = device
        
        self.wr(b'\x1b[999;999H\x1b[6n')
        pos = b''
        char = self.rd() 
        while char != b'R':
            pos += char
            char = self.rd()
        (self.height, self.width) = [int(i, 10) for i in pos[2:].split(b';')]
        self.height -= 1
        self.wr(b'\x1b[?9h') 
    def deinit_tty(self):
        
        self.goto(self.height, 0)
        self.clear_to_eol()
        self.wr(b'\x1b[?9l') 
        if sys.platform == "pyboard" and not Editor.sdev:
            Editor.serialcomm.setinterrupt(3)
    def expandtabs(self, s):
        if '\t' in s:
            sb = _io.StringIO()
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
def pye(content = None, tab_size = 4, device = 0, baud = 115200):
    e = Editor(tab_size)
    if type(content) == str: 
        e.fname = content
        if e.fname: 
            try:
                with open(e.fname) as f:
                    e.content = f.readlines()
                if not e.content: 
                    e.content = [""]
            except Exception as err:
                print ('Could not load %s, Reason: "%s"' % (e.fname, err))
                del e
                return
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        
        e.content = content
    e.init_tty(device, baud)
    e.edit_loop()
    e.deinit_tty()
    if e.fname == None:
        content = e.content
    else:
        content = e.fname
    del e
    gc.collect()
    return content
