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
    b"\x03" : 0x04, 
    b"\r" : 0x0a,
    b"\x7f" : 0x08, 
    b"\x1b[3~": 0x7f,
    b"\x1b[Z" : 0x15, 
    b"\x1b[3;5~": 0x18, 
    b"\x11" : 0x11, 
    b"\n" : 0x0a,
    b"\x08" : 0x08,
    b"\x13" : 0x13, 
    b"\x06" : 0x06, 
    b"\x0e" : 0x0e, 
    b"\x07" : 0x07, 
    b"\x05" : 0x05, 
    b"\x1a" : 0x1a, 
    b"\x09" : 0x09,
    b"\x15" : 0x15, 
    b"\x12" : 0x12, 
    b"\x18" : 0x18, 
    b"\x16" : 0x16, 
    b"\x04" : 0x04, 
    b"\x0c" : 0x0c, 
    b"\x14" : 0x14, 
    b"\x02" : 0x02, 
    b"\x1b[M" : 0x1b,
    b"\x01" : 0x01, 
    b"\x1b[1;5H": 0x14,
    b"\x1b[1;5F": 0x02,
    b"\x0f" : 0x0f, 
    b"\x0b" : 0xfffe,
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
        self.replc_pattern = ""
        self.write_tabs = "n"
    if sys.platform == "pyboard":
        def wr(self,s):
            ns = 0
            while ns < len(s): 
                res = self.serialcomm.write(s[ns:])
                if res != None:
                    ns += res
        def rd(self):
            while not self.serialcomm.any():
                pass
            return self.serialcomm.read(1)
        def not_pending(self):
            return not self.serialcomm.any()
        def init_tty(self, device, baud):
            import pyb
            self.sdev = device
            if self.sdev:
                self.serialcomm = pyb.UART(device, baud)
            else:
                self.serialcomm = pyb.USB_VCP()
                self.serialcomm.setinterrupt(-1)
        def deinit_tty(self):
            if not self.sdev:
                self.serialcomm.setinterrupt(3)
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
    def mouse_reporting(self, onoff):
        self.wr('\x1b[?9h' if onoff else '\x1b[?9l') 
    def scroll_region(self, stop):
        self.wr('\x1b[1;{}r'.format(stop) if stop else '\x1b[r') 
    def scroll_up(self, scrolling):
        self.scrbuf[scrolling:] = self.scrbuf[:-scrolling]
        self.scrbuf[:scrolling] = [''] * scrolling
        self.goto(0, 0)
        self.wr("\x1bM" * scrolling)
    def scroll_down(self, scrolling):
        self.scrbuf[:-scrolling] = self.scrbuf[scrolling:]
        self.scrbuf[-scrolling:] = [''] * scrolling
        self.goto(self.height - 1, 0)
        self.wr("\x1bD " * scrolling)
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
                else: 
                    self.mouse_fct = ord((self.rd())) 
                    self.mouse_x = ord(self.rd()) - 33
                    self.mouse_y = ord(self.rd()) - 33
                    if self.mouse_fct == 0x61:
                        return 0x1d
                    elif self.mouse_fct == 0x60:
                        return 0x1c
                    else:
                        return 0x1b 
            elif len(in_buffer) == 1: 
                return in_buffer[0]
    def display_window(self): 
        self.cur_line = min(self.total_lines - 1, max(self.cur_line, 0))
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
            else:
                match = self.content[line][spos:].find(pattern)
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
        if key == 0x0d:
            if self.cur_line < self.total_lines - 1:
                self.cur_line += 1
                if self.cur_line == self.top_line + self.height:
                    self.scroll_down(1)
        elif key == 0x0b:
            if self.cur_line > 0:
                self.cur_line -= 1
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
        elif key == 0x1f:
            if self.col == 0 and self.cur_line > 0:
                self.cur_line -= 1
                self.col = len(self.content[self.cur_line])
                if self.cur_line < self.top_line:
                    self.scroll_up(1)
            else:
                if self.col > 0: self.col -= 1
        elif key == 0x1e:
                self.col += 1
        elif key == 0x10:
            self.col = self.spaces(self.content[self.cur_line]) if self.col == 0 else 0
        elif key == 0x03:
            self.col = len(self.content[self.cur_line])
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
        elif key == 0x01: 
            self.autoindent = 'y' if self.autoindent != 'y' else 'n'
            self.autoindent = 'y' if self.autoindent != 'y' else 'n'
            pat = self.line_edit("Case Sensitive Search {}, Autoindent {}, Tab Size {}, Write Tabs {}: ".format(self.case, self.autoindent, self.tab_size, self.write_tabs), "")
            try:
                res = [i.strip().lower() for i in pat.split(",")]
                if res[0]: self.case = 'y' if res[0][0] == 'y' else 'n'
                if res[1]: self.autoindent = 'y' if res[1][0] == 'y' else 'n'
                if res[2]:
                    try: self.tab_size = int(res[2])
                    except: pass
                if res[3]: self.write_tabs = 'y' if res[3][0] == 'y' else 'n'
            except:
                pass
        elif key == 0x1b: 
            if self.mouse_y < self.height:
                self.col = self.mouse_x + self.margin
                self.cur_line = self.mouse_y + self.top_line
                if self.mouse_fct in (0x22, 0x30): 
                    self.mark = self.cur_line if self.mark == None else None
        elif key == 0x1c: 
            if self.top_line > 0:
                self.top_line = max(self.top_line - 3, 0)
                self.cur_line = min(self.cur_line, self.top_line + self.height - 1)
                self.scroll_up(3)
        elif key == 0x1d: 
            if self.top_line + self.height < self.total_lines:
                self.top_line = min(self.top_line + 3, self.total_lines - 1)
                self.cur_line = max(self.cur_line, self.top_line)
                self.scroll_down(3)
        elif key == 0xfffe:
            if self.col >= len(self.content[self.cur_line]): 
                return True
            opening = "([{<"
            closing = ")]}>"
            level = 0
            pos = self.col
            srch = self.content[self.cur_line][pos]
            i = opening.find(srch)
            if i >= 0: 
                pos += 1
                match = closing[i]
                for i in range(self.cur_line, self.total_lines):
                    for c in range(pos, len(self.content[i])):
                        if self.content[i][c] == match:
                            if level == 0: 
                                self.cur_line = i
                                self.col = c
                                return True 
                            else:
                                level -= 1
                        elif self.content[i][c] == srch:
                            level += 1
                    pos = 0 
            else:
                i = closing.find(srch)
                if i >= 0: 
                    pos -= 1
                    match = opening[i]
                    for i in range(self.cur_line, -1, -1):
                        for c in range(pos, -1, -1):
                            if self.content[i][c] == match:
                                if level == 0: 
                                    self.cur_line = i
                                    self.col = c
                                    return True 
                                else:
                                    level -= 1
                            elif self.content[i][c] == srch:
                                level += 1
                        if i > 0: 
                            pos = len(self.content[i - 1]) - 1
        elif key == 0x14: 
            self.cur_line = 0
        elif key == 0x02: 
            self.cur_line = self.total_lines - 1
            self.row = self.height - 1 
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
        if yank: self.yank_buffer = self.content[lrange[0]:lrange[1]]
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
        jut = self.col - len(l) 
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
            self.content[self.cur_line:self.cur_line] = [' ' * ni + l[self.col:]] if jut < 0 else [""]
            self.total_lines += 1
            self.col = ni
            self.mark = None 
        elif key == 0x08:
            if self.mark != None:
                self.delete_lines(False)
            elif self.col > 0:
                if jut <= 0: 
                    self.undo_add(self.cur_line, [l], 0x08)
                    self.content[self.cur_line] = l[:self.col - 1] + l[self.col:]
                self.col -= 1
            elif self.cur_line > 0: 
                self.undo_add(self.cur_line - 1, [self.content[self.cur_line - 1], l], 0)
                self.col = len(self.content[self.cur_line - 1])
                self.content[self.cur_line - 1] += self.content.pop(self.cur_line)
                self.cur_line -= 1
                self.total_lines -= 1
        elif key == 0x7f:
            if self.mark != None:
                self.delete_lines(False)
            elif jut < 0:
                self.undo_add(self.cur_line, [l], 0x7f)
                self.content[self.cur_line] = l[:self.col] + l[self.col + 1:]
            elif (self.cur_line + 1) < self.total_lines: 
                self.undo_add(self.cur_line, [l, self.content[self.cur_line + 1]], 0)
                if jut > 0: 
                    l += ' ' * jut
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
                ni = self.tab_size - self.col % self.tab_size 
                if jut < 0:
                    self.undo_add(self.cur_line, [l], 0x09)
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
                ni = (self.col - 1) % self.tab_size + 1
                if jut < 0:
                    ni = min(ni, self.spaces(l, self.col)) 
                    if ni > 0:
                        self.undo_add(self.cur_line, [l], 0x15)
                        self.content[self.cur_line] = l[:self.col - ni] + l[self.col:]
                        self.col -= ni
                else:
                    self.col -= min(ni, jut)
        elif key == 0x12:
            count = 0
            pat = self.line_edit("Replace: ", self.find_pattern)
            if pat:
                rpat = self.line_edit("With: ", self.replc_pattern)
                if rpat != None: 
                    self.replc_pattern = rpat
                    q = ''
                    cur_line = self.cur_line 
                    if self.mark != None: 
                        (self.cur_line, end_line) = self.line_range()
                        self.col = 0
                    else: 
                        end_line = self.total_lines
                    self.message = "Replace (yes/No/all/quit) ? "
                    while True: 
                        ni = self.find_in_file(pat, self.col, end_line)
                        if ni: 
                            if q != 'a':
                                self.display_window()
                                key = self.get_input() 
                                q = chr(key).lower()
                            if q == 'q' or key == 0x11:
                                break
                            elif q in ('a','y'):
                                self.undo_add(self.cur_line, [self.content[self.cur_line]], 0)
                                self.content[self.cur_line] = self.content[self.cur_line][:self.col] + rpat + self.content[self.cur_line][self.col + ni:]
                                self.col += len(rpat)
                                count += 1
                            else: 
                                self.col += 1
                        else: 
                            break
                    self.cur_line = cur_line
                    self.message = "'{}' replaced {} times".format(pat, count)
        elif key == 0x0f:
            fname = self.line_edit("Insert File: ", "")
            if fname:
                (content, self.message) = self.get_file(fname)
                if content:
                    self.undo_add(self.cur_line, None, 0, -len(content))
                    self.content[self.cur_line:self.cur_line] = content
                    self.total_lines = len(self.content)
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
                if self.mark != None:
                    fname = self.line_edit("Save Mark: ", "")
                    lrange = self.line_range()
                else:
                    fname = self.fname
                    if fname == None:
                        fname = ""
                    fname = self.line_edit("Save File: ", fname)
                    lrange = (0, self.total_lines)
            if fname:
                try:
                    with open("tmpfile.pye", "w") as f:
                        for l in self.content[lrange[0]:lrange[1]]:
                            if self.write_tabs == 'y':
                                f.write(self.packtabs(l) + '\n')
                            else:
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
            if jut >= 0:
                if key != 0x20:
                    self.undo_add(self.cur_line, [l], 0x41)
                    self.content[self.cur_line] = l + ' ' * jut + chr(key)
            else:
                self.undo_add(self.cur_line, [l], 0x20 if key == 0x20 else 0x41)
                self.content[self.cur_line] = l[:self.col] + chr(key) + l[self.col:]
            self.col += 1
    def edit_loop(self): 
        if self.content == []: 
            self.content = [""]
        self.total_lines = len(self.content)
        self.set_screen_parms()
        self.mouse_reporting(True) 
        self.scroll_region(self.height)
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
                    self.mouse_reporting(False) 
                    self.scroll_region(0)
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
            except:
                self.message = "Oops!"
    def packtabs(self, s):
        from _io import StringIO
        sb = StringIO()
        for i in range(0, len(s), 8):
            c = s[i:i + 8]
            cr = c.rstrip(" ")
            if c != cr: 
                sb.write(cr + "\t") 
            else:
                sb.write(c)
        return sb.getvalue()
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
    e.init_tty(device, baud)
    e.edit_loop()
    e.deinit_tty()
    return e.content if (e.fname == None) else e.fname
