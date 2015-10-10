import sys
import gc
import _io
if sys.platform == "pyboard":
    import pyb
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
    b"\x05" : 0x05, 
    b"\x09" : 0x09,
    b"\x01" : 0x01, 
    b"\x14" : 0x02, 
    b"\x1b[1;5H": 0x02,
    b"\x02" : 0x14, 
    b"\x1b[1;5F": 0x14,
    b"\x1b[Z" : 0x15, 
    b"\x15" : 0x15, 
    b"\x1b[3;5~": 0x18,
    b"\x18" : 0x18, 
    b"\x16" : 0x16, 
    b"\x12" : 0x12, 
    b"\x04" : 0x04, 
    b"\x1a" : 0x1a, 
    b"\x0f" : 0x1e, 
    }
    def __init__(self, tab_size, undo_limit):
        self.top_line = 0
        self.cur_line = 0
        self.row = 0
        self.col = 0
        self.margin = 0
        self.scrolling = 0
        self.tab_size = tab_size
        self.changed = ' '
        self.sticky_c = " "
        self.message = ""
        self.find_pattern = ""
        self.replc_pattern = ""
        self.y_buffer = []
        self.content = [""]
        self.fname = None
        self.lastkey = 0
        self.autoindent = "y"
        self.write_tabs = "n"
        self.case = "n"
        self.undo = []
        self.undo_limit = max(undo_limit, 0)
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
    
        Editor.wr('\x1b[999;999H\x1b[6n')
        pos = b''
        char = Editor.rd() 
        while char != b'R':
            pos += char
            char = Editor.rd()
        (height, width) = [int(i, 10) for i in pos[2:].split(b';')]
        return (height-1, width)
    @staticmethod
    def mouse_reporting(onoff):
        if onoff:
            Editor.wr('\x1b[?9h') 
        else:
            Editor.wr('\x1b[?9l') 
    @staticmethod
    def scroll_region(stop):
        if stop:
            Editor.wr('\x1b[1;%dr' % stop) 
        else:
            Editor.wr('\x1b[r') 
    @staticmethod
    def scroll_lines(updown, lines):
        if updown:
            Editor.wr("\x1bM" * lines) 
        else:
            Editor.wr("\x1bD " * lines) 
    def print_no(self, row, lnum):
        Editor.goto(row, 0)
        if self.col_width > 0:
            Editor.hilite(2)
            Editor.wr(lnum)
            Editor.hilite(0)
    def set_screen_parms(self, lines, lnum):
        (self.height, self.width) = self.get_screen_size()
        self.scroll_region(self.height)
        self.scrbuf = ["\x04"] * self.height 
        if lnum: 
            lnum = 3
            if self.total_lines > 900: lnum = 4
            if self.total_lines > 9000: lnum = 5
            self.col_width = lnum + 1 
            self.col_fmt = "%%%dd " % lnum
            self.col_spc = " " * self.col_width
            self.width -= self.col_width
        else:
            self.col_width = 0
            self.col_fmt = "[%d]"
            self.col_spc = ''
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
            self.scroll_lines(True, -self.scrolling)
        elif self.scrolling > 0: 
            self.scrbuf[:-self.scrolling] = self.scrbuf[self.scrolling:]
            self.scrbuf[-self.scrolling:] = [''] * self.scrolling
            self.goto(self.height - 1, 0)
            self.scroll_lines(False, self.scrolling)
        self.scrolling = 0
        i = self.top_line
        for c in range(self.height):
            if i == self.total_lines: 
                if self.scrbuf[c] != '':
                    self.print_no(c, self.col_spc)
                    self.clear_to_eol()
                    self.scrbuf[c] = ''
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
            self.wr(self.col_fmt % self.total_lines)
            self.wr("%c Row: %d Col: %d  %s" % (self.changed, self.cur_line + 1, self.col + 1, self.message))
            self.hilite(0)
        self.cursor(True)
        self.goto(self.row, self.col - self.margin + self.col_width)
    def clear_status(self):
        if (self.status != "y") and self.message:
            self.goto(self.height, 0)
            self.clear_to_eol()
        self.message = ''
    @staticmethod
    def spaces(line, pos = 0): 
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
            elif key == 0x08: 
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == 0x1f: 
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: 
                if len(prompt) + len(res) < self.width - 1:
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
            else:
                match = self.content[line][spos:].find(pattern)
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
        if key == 0x0d:
            if self.cur_line < self.total_lines - 1:
                self.cur_line += 1
                if self.cur_line == self.top_line + self.height: self.scrolling = 1
        elif key == 0x0b:
            if self.cur_line > 0:
                if self.cur_line == self.top_line: self.scrolling = -1
                self.cur_line -= 1
        elif key == 0x0c:
            self.col -= 1
        elif key == 0x0f:
            self.col += 1
        elif key == 0x10:
            ns = self.spaces(self.content[self.cur_line])
            self.col = ns if (self.col > ns) else 0
        elif key == 0x11:
            ns = self.spaces(self.content[self.cur_line])
            self.col = ns if (self.col < ns) else len(self.content[self.cur_line])
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
            pat = self.line_edit("Case Sensitive Search %c, Autoindent %c, Statusline %c, Write Tabs %c: " %
                  (self.case, self.autoindent, self.status, self.write_tabs), "")
            try:
                res = [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case = res[0][0]
                if res[1]: self.autoindent = res[1][0]
                if res[2]: self.status = res[2][0]
                if res[3]: self.write_tabs = res[3][0]
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
    def undo_add(self, lnum, text, key, span = 1):
        if self.undo_limit > 0 and (
           len(self.undo) == 0 or key == 0 or self.undo[-1][3] != key or self.undo[-1][0] != lnum):
            if len(self.undo) >= self.undo_limit: 
                del self.undo[0]
                self.sticky_c = "*"
            self.undo.append((lnum, span, text, key))
    def handle_edit_key(self, key): 
        l = self.content[self.cur_line]
        if key == 0x0a:
            self.undo_add(self.cur_line, [l], 0, 2)
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
            self.changed = '*'
        elif key == 0x08:
            if self.col > 0:
                ni = 1
                self.undo_add(self.cur_line, [l], key)
                if self.autoindent == "y" and self.spaces(l, 0) == self.col: 
                    ni = (self.col - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                self.col -= ni
                self.changed = '*'
            elif self.cur_line: 
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], 0)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += l
                del self.content[self.cur_line]
                self.cur_line -= 1
                self.total_lines -= 1
                self.changed = '*'
        elif key == 0x1f:
            if self.col < len(l):
                self.undo_add(self.cur_line, [l], key)
                l = l[:self.col] + l[self.col + 1:]
                self.content[self.cur_line] = l
                self.changed = '*'
            elif (self.cur_line + 1) < self.total_lines: 
                ni = 0
                if self.autoindent == "y": 
                    ni = self.spaces(self.content[self.cur_line + 1])
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], 0)
                self.content[self.cur_line] = l + self.content.pop(self.cur_line + 1)[ni:]
                self.total_lines -= 1
                self.changed = '*'
        elif key == 0x09: 
            self.undo_add(self.cur_line, [l], key)
            ns = self.spaces(l, 0)
            if ns and self.col < ns: 
                ni = self.tab_size - ns % self.tab_size
            else:
                ni = self.tab_size - self.col % self.tab_size
            self.content[self.cur_line] = l[:self.col] + ' ' * ni + l[self.col:]
            if ns == len(l) or self.col >= ns: 
                self.col += ni 
            self.changed = '*'
        elif key == 0x15: 
            self.undo_add(self.cur_line, [l], key)
            ns = self.spaces(l, 0)
            if ns and self.col < ns: 
                ni = (ns - 1) % self.tab_size + 1
                self.content[self.cur_line] = l[ni:]
                self.changed = '*'
            else: 
                ns = self.spaces(l, self.col)
                ni = (self.col - 1) % self.tab_size + 1
                if (ns >= ni):
                    self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                    self.col -= ni
                    self.changed = '*'
        elif key == 0x18: 
            self.undo_add(self.cur_line, [l], 0, 0)
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
            self.changed = '*'
        elif key == 0x04: 
            if key == self.lastkey: 
                self.y_buffer.append(l) 
            else:
                del self.y_buffer 
                self.y_buffer = [l]
            if self.cur_line + 1 < self.total_lines:
                self.cur_line += 1
        elif key == 0x16: 
            if self.y_buffer:
                self.undo_add(self.cur_line, None, 0, -len(self.y_buffer))
                self.content[self.cur_line:self.cur_line] = self.y_buffer 
                self.total_lines += len(self.y_buffer)
                self.changed = '*'
        elif key == 0x12:
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
                                key = self.get_input() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x03:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], 0)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                                self.changed = '*'
                            else: 
                                self.col += 1
                        else:
                            break
                    self.message = "'%s' replaced %d times" % (pat, count)
        elif key == 0x1e:
            fname = self.line_edit("Insert File: ", "")
            if fname:
                (content, self.message) = self.get_file(fname)
                if content:
                    self.undo_add(self.cur_line, None, 0, -len(content))
                    self.content[self.cur_line:self.cur_line] = content
                    self.total_lines = len(self.content)
                    del content
                    self.changed = "*"
        elif key == 0x13:
            fname = self.fname
            if fname == None:
                fname = ""
            fname = self.line_edit("File Name: ", fname)
            if fname:
                try:
                    with open(fname, "w") as f:
                        for l in self.content:
                            f.write(self.packtabs(l) + '\n' if self.write_tabs == 'y' else l + '\n')
                    self.changed = " " 
                    self.sticky_c = " " 
                    del self.undo[:]
                    self.fname = fname 
                except:
                    pass
        elif key == 0x1a:
            if len(self.undo) > 0:
                action = self.undo.pop(-1) 
                self.cur_line = action[0]
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
            self.changed = '*'
    def edit_loop(self, lnum): 
        self.total_lines = len(self.content)
        self.set_screen_parms(self.total_lines, lnum)
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
            elif key == 0x05:
                del self.scrbuf
                self.set_screen_parms(self.total_lines, lnum)
                self.row = min(self.height - 1, self.row)
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
        self.mouse_reporting(True) 
    def deinit_tty(self):
        
        self.mouse_reporting(False) 
        self.scroll_region(0)
        self.goto(self.height, 0)
        self.clear_to_eol()
        if sys.platform == "pyboard" and not Editor.sdev:
            Editor.serialcomm.setinterrupt(3)
    @staticmethod
    def expandtabs(s):
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
    @staticmethod
    def packtabs(s):
        sb = _io.StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if c != cr: 
                sb.write(cr + "\t") 
            else:
                sb.write(c)
        return sb.getvalue()
    @staticmethod
    def get_file(fname):
        try:
                with open(fname) as f:
                    content = f.readlines()
        except Exception as err:
            message = 'Could not load %s, Reason: "%s"' % (fname, err)
            return (None, message)
        else:
            if not content: 
                content = [""]
        for i in range(len(content)): 
            content[i] = Editor.expandtabs(content[i].rstrip('\r\n\t '))
        return (content, "")
def pye(content = None, tab_size = 4, lnum = 4, undo = 50, device = 0, baud = 115200, fd_tty = 0):
    e = Editor(tab_size, undo)
    if type(content) == str and content: 
        e.fname = content
        (e.content, e.message) = e.get_file(e.fname)
        if not e.content: 
            print (e.message)
            del e
            return
    elif type(content) == list and len(content) > 0 and type(content[0]) == str:
        
        e.content = content
        if fd_tty:
            e.fname = ""
    e.init_tty(device, baud, fd_tty)
    e.edit_loop(lnum)
    e.deinit_tty()
    content = e.content if (e.fname == None) else e.fname
    del e
    gc.collect()
    return content
