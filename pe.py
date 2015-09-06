import sys
import gc
import _io
if sys.platform == "pyboard":
    import pyb
class Editor:
    KEYMAP = { 
    b"\x1b[A" : 0x05,
    b"\x1b[B" : 0x0b,
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
    b"\x03" : 0x03, 
    b"\r" : 0x0a,
    b"\n" : 0x0a,
    b"\x7f" : 0x08, 
    b"\x08" : 0x08,
    b"\x1b[3~": 0x1f,
    b"\x13" : 0x13, 
    b"\x06" : 0x06, 
    b"\x0e" : 0x0e, 
    b"\x07" : 0x07, 
    b"\x1b[M" : 0x1b,
    b"\x01" : 0x01, 
    b"\x14" : 0x02, 
    b"\x1b[1;5H": 0x02,
    b"\x02" : 0x14, 
    b"\x1b[1;5F": 0x14,
    b"\x1b[3;5~": 0x18,
    b"\x18" : 0x18, 
    b"\x09" : 0x09,
    b"\x1b[Z" : 0x15, 
    b"\x15" : 0x15, 
    b"\x16" : 0x16, 
    b"\x12" : 0x12, 
    b"\x04" : 0x04, 
    }
    def __init__(self, tab_size):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.col_width = 0
        self.col_fmt = "%d\t" 
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
    def hilite(mode):
        if mode == 1:
            Editor.wr(b"\x1b[1m")
        elif mode == 2:
            Editor.wr(b"\x1b[2;7m")
        else:
            Editor.wr(b"\x1b[0m")
    def print_no(self, row, line):
        self.goto(row, 0)
        if self.col_width > 1:
            self.hilite(2)
            if line:
                self.wr(line)
            else:
                self.wr(self.col_spc)
            self.hilite(0)
    def get_input(self): 
        while True:
            input = Editor.rd()
            if input == b'\x1b': 
                while True:
                    input += Editor.rd()
                    c = chr(input[-1])
                    if c == '~' or (c.isalpha() and c != 'O'):
                        break
            if input in self.KEYMAP:
                c = self.KEYMAP[input]
                if c == 0x1b: 
                    mf = ord((Editor.rd())) & 0xe3 
                    self.mouse_x = ord(Editor.rd()) - 33
                    self.mouse_y = ord(Editor.rd()) - 33
                    if mf == 0x61:
                        return 0x1d
                    elif mf == 0x60:
                        return 0x1c
                    else:
                        return 0x1b 
                else:
                    return c
            elif input[0] >= 0x20: 
                return input[0]
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
        if self.scrolling < 0: 
            self.scrbuf[-self.scrolling:] = self.scrbuf[:self.scrolling]
            self.scrbuf[:-self.scrolling] = [''] * -self.scrolling
            self.goto(0, 0)
            self.wr("\x1bM" * -self.scrolling)
        elif self.scrolling > 0: 
            self.scrbuf[:-self.scrolling] = self.scrbuf[self.scrolling:]
            self.scrbuf[-self.scrolling:] = [''] * self.scrolling
            self.goto(self.height - 1, 0)
            self.wr("\x1bD " * self.scrolling)
        self.scrolling = 0
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: 
                if self.scrbuf[c] != '\x04':
                    self.print_no(c, None)
                    self.clear_to_eol()
                    self.scrbuf[c] = '\x04'
            else:
                l = self.content[i][self.margin:self.margin + self.width]
                lnum = self.col_fmt % (i + 1)
                if (lnum + l) != self.scrbuf[c]: 
                    self.print_no(c, lnum) 
                    self.wr(l)
                    if len(l) < self.width:
                        self.clear_to_eol()
                    self.scrbuf[c] = lnum + l
                i += 1
        if self.status == "y" or self.message:
            self.goto(self.height, 0)
            self.clear_to_eol() 
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
    def spaces(self, line, pos = 0): 
        if pos: 
            return len(line[:pos]) - len(line[:pos].rstrip(" "))
        else: 
            return len(line) - len(line.lstrip(" "))
    def line_edit(self, prompt, default): 
        self.goto(self.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' 
        while True:
            key = self.get_input() 
            if key in (0x0a, 0x09): 
                self.hilite(0)
                return res
            elif key == 0x03: 
                self.hilite(0)
                return None
            elif key in (0x08, 0x1f): 
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key >= 0x20: 
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
        if key == 0x0b:
            if self.cur_line < self.total_lines - 1:
                self.cur_line += 1
                if self.cur_line == self.top_line + self.height: self.scrolling = 1
        elif key == 0x05:
            if self.cur_line > 0:
                if self.cur_line == self.top_line: self.scrolling = -1
                self.cur_line -= 1
        elif key == 0x0c:
            self.col -= 1
        elif key == 0x0f:
            self.col += 1
        elif key == 0x10:
            ns = self.spaces(self.content[self.cur_line])
            if self.col > ns:
                self.col = ns
            else:
                self.col = 0
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
                self.row = self.row = self.height >> 1
        elif key == 0x07: 
            line = self.line_edit("Goto Line: ", "")
            if line:
                try:
                    self.cur_line = int(line) - 1
                    self.row = self.height >> 1
                except:
                    pass
        elif key == 0x1b: 
            if self.mouse_y < self.height:
                self.col = self.mouse_x + self.margin - self.col_width
                self.cur_line = self.mouse_y + self.top_line
            self.message = ' '
        elif key == 0x1c: 
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + self.height - 1)
                self.scrolling = -3
        elif key == 0x1d: 
            if self.top_line + self.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scrolling = 3
        elif key == 0x01: 
            pat = self.line_edit("Case Sensitive Search %c, Statusline %c, Autoindent %c: " % (self.case, self.status, self.autoindent), "")
            try:
                res = [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case = res[0][0]
                if res[1]: self.status = res[1][0]
                if res[2]: self.autoindent = res[2][0]
            except:
                pass
        elif key == 0x02: 
            self.cur_line = 0
        elif key == 0x14: 
            self.cur_line = self.total_lines - 1
            self.row = self.height - 1
            self.message = ' ' 
        else:
            return False
        return True
    def handle_edit_key(self, key): 
        l = self.content[self.cur_line]
        sc = self.changed
        self.changed = '*'
        if key == 0x0a:
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
        elif key == 0x08:
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
        elif key == 0x1f:
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
        elif key == 0x09: 
            ns = self.spaces(l, 0)
            if ns and self.col < ns: 
                ni = self.tab_size - ns % self.tab_size
            else:
                ni = self.tab_size - self.col % self.tab_size
            self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
            if ns == len(l) or self.col >= ns: 
                self.col += ni 
        elif key == 0x15: 
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
        elif key == 0x18: 
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
        elif key == 0x04: 
            if key == self.lastkey: 
                self.y_buffer.append(l) 
            else:
                del self.y_buffer 
                self.y_buffer = [l]
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
            self.changed = sc
        elif key == 0x16: 
            if self.y_buffer:
                self.content[self.cur_line:self.cur_line] = self.y_buffer 
                self.total_lines += len(self.y_buffer)
            else:
                self.changed = sc
        elif key == 0x12:
            count = 0
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
                            if q != 'a':
                                self.message = "Replace (yes/No/all/quit) ? "
                                self.display_window()
                                key = self.get_input() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x03:
                                break
                            elif q in ('a','y'):
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                                self.changed = '*'
                            else: 
                                self.col += 1
                        else:
                            break
                    if count:
                        self.message = "'%s' replaced %d times" % (pat, count)
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
                    self.fname = fname
                except:
                    pass
            else:
                self.changed = sc
        elif key >= 0x20:
            self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
        else: 
            self.changed = sc
    def edit_loop(self, lnum): 
        self.scrbuf = [""] * self.height
        self.total_lines = len(self.content)
        if lnum: 
            lnum = 3
            if self.total_lines > 900: lnum = 4
            if self.total_lines > 9000: lnum = 5
            self.col_width = lnum + 1 
            self.col_fmt = "%%%dd " % lnum
            self.col_spc = " " * self.col_width
            self.width -= self.col_width
        
        for i in range(self.total_lines):
            self.content[i] = self.expandtabs(self.content[i].rstrip('\r\n\t '))
        while True:
            self.display_window() 
            key = self.get_input() 
            self.clear_status() 
            if key == 0x03:
                if self.changed != ' ' and self.fname != None:
                    res = self.line_edit("Content changed! Quit without saving (y/N)? ", "N")
                    if not res or res[0].upper() != 'Y':
                        continue
                return None
            elif self.handle_cursor_keys(key):
                pass
            else: self.handle_edit_key(key)
            self.lastkey = key
    def init_tty(self, device, baud, fd_tty):
        if sys.platform == "pyboard":
            if (device):
                Editor.serialcomm = pyb.UART(device, baud)
                self.status = "n"
            else:
                Editor.serialcomm = pyb.USB_VCP()
                Editor.serialcomm.setinterrupt(-1)
                self.status = "y"
            Editor.sdev = device
        
        self.wr('\x1b[999;999H\x1b[6n')
        pos = b''
        char = Editor.rd() 
        while char != b'R':
            pos += char
            char = Editor.rd()
        (self.height, self.width) = [int(i, 10) for i in pos[2:].split(b';')]
        self.height -= 1
        self.wr('\x1b[?9h') 
        self.wr('\x1b[1;%dr' % self.height) 
    def deinit_tty(self):
        
        self.wr('\x1b[?9l\x1b[r') 
        self.goto(self.height, 0)
        self.clear_to_eol()
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
def pye(content = None, tab_size = 4, lnum = 4, device = 0, baud = 115200, fd_tty = 0):
    e = Editor(tab_size)
    if type(content) == str: 
        e.fname = content
        if e.fname: 
            try:
                    with open(e.fname) as f:
                        e.content = f.readlines()
            except Exception as err:
                print ('Could not load %s, Reason: "%s"' % (e.fname, err))
                del e
                return
            else:
                if not e.content: 
                    e.content = [""]
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        
        e.content = content
        if fd_tty: e.fname = ""
    e.init_tty(device, baud, fd_tty)
    e.edit_loop(lnum)
    e.deinit_tty()
    if e.fname == None:
        content = e.content
    else:
        content = e.fname
    del e
    gc.collect()
    return content
