#
# This is the regex version of find.
    def find_in_file(self, pattern, col, end):
        Editor.find_pattern = pattern ## remember it
        if Editor.case != "y":
            pattern = pattern.lower()
        try:
            rex = re_compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return None
        start = self.cur_line
        if (col > len(self.content[start]) or   # After EOL
            (pattern[0] == '^' and col != 0)):  # or anchored and not at BOL
            start, col = start + 1, 0           # Skip to the next line
        for line in range(start, end):
            l = self.content[line][col:]
            if Editor.case != "y":
                l = l.lower()
            match = rex.search(l)
            if match: # Bingo
                self.cur_line = line
## Instead of match.span, a simple find has to be performed to get the cursor position.
## And '$' has to be treated separately, so look for a true EOL match first
                if pattern[-1:] == "$" and match.group(0)[-1:] != "$":
                    self.col = col + len(l) - len(match.group(0))
                else:
                    self.col = col + l.find(match.group(0))
                return len(match.group(0))
            col = 0
        else:
            self.message = pattern + " not found (again)"
            return None

# this is the simple version of find
    def find_in_file(self, pattern, pos, end):
        Editor.find_pattern = pattern  # remember it
        if Editor.case != "y":
            pattern = pattern.lower()
        spos = pos
        for line in range(self.cur_line, end):
            if Editor.case != "y":
                match = self.content[line][spos:].lower().find(pattern)
            else:
                match = self.content[line][spos:].find(pattern)
            if match >= 0: # Bingo!
                self.col = match + spos
                self.cur_line = line
                return len(pattern)
            spos = 0
        else:
            self.message = "No match: " + pattern
            return None

    def line_edit(self, prompt, default, zap=None):  ## better one: added cursor keys and backsp, delete
        push_msg = lambda msg: self.wr(msg + "\b" * len(msg)) ## Write a message and move cursor back
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        pos = len(res)
        while True:
            key, char = self.get_input()  ## Get Char of Fct.
            if key == KEY_NONE:  ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + char + res[pos:]
                    self.wr(res[pos])
                    pos += len(char)
                    push_msg(res[pos:])  ## update tail
            elif key in (KEY_ENTER, KEY_TAB):  ## Finis
                self.hilite(0)
                return res
            elif key in (KEY_QUIT, KEY_COPY):  ## Abort
                self.hilite(0)
                return None
            elif key == KEY_LEFT:
                if pos > 0:
                    self.wr("\b")
                    pos -= 1
            elif key == KEY_RIGHT:
                if pos < len(res):
                    self.wr(res[pos])
                    pos += 1
            elif key == KEY_HOME:
                self.wr("\b" * pos)
                pos = 0
            elif key == KEY_END:
                self.wr(res[pos:])
                pos = len(res)
            elif key == KEY_DELETE:  ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ')  ## update tail
            elif key == KEY_BACKSPACE:  ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    push_msg(res[pos:] + ' ')  ## update tail
            elif key == KEY_PASTE:  ## Get from content
                self.wr('\b' * pos + ' ' * len(res) + '\b' * len(res))
                res = self.getsymbol(self.content[self.cur_line], self.col, zap)
                self.wr(res)
                pos = len(res)

    def line_edit(self, prompt, default):  # simple one: only 4+1 fcts
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        while True:
            key, char = self.get_input()  # Get Char of Fct.
            if key == KEY_NONE:  ## character to be added
                if len(prompt) + len(res) < Editor.width - 2:
                    res += char
                    self.wr(char)
            elif key in (KEY_ENTER, KEY_TAB):  # Finis
                self.hilite(0)
                return res
            elif key == KEY_QUIT:  # Abort
                self.hilite(0)
                return None
            elif key == KEY_BACKSPACE:  # Backspace
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == KEY_DELETE:  # Delete prev. Entry
                self.wr('\b \b' * len(res))
                res = ''

    def expandtabs(self, s, tabsize=8):
        import _io
        if '\t' in s and tabsize > 0:
            sb = _io.StringIO()
            pos = 0
            for c in s:
                if c == '\t':  # tab is seen
                    sb.write(" " * (tabsize - pos % tabsize))  # replace by space
                    pos += tabsize - pos % tabsize
                else:
                    sb.write(c)
                    pos += 1
            return sb.getvalue()
        else:
            return s

    def packtabs(self, s, tabsize=8):
        if tabsize > 0:
            sb = _io.StringIO()
            for i in range(0, len(s), tabsize):
                c = s[i:i + tabsize]
                cr = c.rstrip(" ")
                if c != cr:  # Spaces at the end of a section
                    sb.write(cr + "\t")  # replace by tab
                else:
                    sb.write(c)
            return sb.getvalue()
        else:
            return s

    def cls(self):
        self.wr(b"\x1b[2J")
