##
## This is the regex version of find.
    def find_in_file(self, pattern, pos, end):
        import re
        self.find_pattern = pattern ## remember it
        if self.case != "y":
            pattern = pattern.lower()
        try:
            rex = re.compile(pattern)
        except:
            self.message = "Invalid pattern: " + pattern
            return False
        spos = pos
        for line in range(self.cur_line, end):
            if self.case != "y":
                match = rex.search(self.content[line][spos:].lower())
            else:
                match = rex.search(self.content[line][spos:])
            if match:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return 0
## micropython does not support span(), therefore a second simple find on the target line
        if self.case != "y":
            self.col = max(self.content[line][spos:].lower().find(match.group(0)), 0) + spos
        else:
            self.col = max(self.content[line][spos:].find(match.group(0)), 0) + spos
        self.cur_line = line
        self.message = ' ' ## force status once
        return len(match.group(0))

    def line_edit(self, prompt, default):  ## better one: added cursor keys and backsp, delete
        push_msg = lambda msg: self.wr(msg + "\b" * len(msg)) ## Write a message and move cursor back
        self.goto(Editor.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        pos = len(res)
        while True:
            key = self.get_input()  ## Get Char of Fct.
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(False)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(False)
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
            elif key == KEY_DELETE: ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    push_msg(res[pos:] + ' ') ## update tail
            elif key == KEY_BACKSPACE: ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    push_msg(res[pos:] + ' ') ## update tail
            elif key >= 0x20: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + chr(key) + res[pos:]
                    self.wr(res[pos])
                    pos += 1
                    push_msg(res[pos:]) ## update tail

    def line_edit(self, prompt, default):  ## simple one: only 4 fcts
        self.goto(Editor.height, 0)
        self.hilite(1)
        self.wr(prompt)
        self.wr(default)
        self.clear_to_eol()
        res = default
        while True:
            key = self.get_input()  ## Get Char of Fct.
            if key in (KEY_ENTER, KEY_TAB): ## Finis
                self.hilite(0)
                return res
            elif key == KEY_QUIT: ## Abort
                self.hilite(0)
                return None
            elif key == KEY_BACKSPACE: ## Backspace
                if (len(res) > 0):
                    res = res[:len(res)-1]
                    self.wr('\b \b')
            elif key == KEY_DELETE: ## Delete prev. Entry
                self.wr('\b \b' * len(res))
                res = ''
            elif key >= 0x20: ## char to be added at the end
                if len(prompt) + len(res) < self.width - 2:
                    res += chr(key)
                    self.wr(chr(key))

    def expandtabs(self, s, tabsize = 8):
        import _io
        if '\t' in s and tabsize > 0:
            sb = _io.StringIO()
            pos = 0
            for c in s:
                if c == '\t': ## tab is seen
                    sb.write(" " * (tabsize - pos % tabsize)) ## replace by space
                    pos += tabsize - pos % tabsize
                else:
                    sb.write(c)
                    pos += 1
            return sb.getvalue()
        else:
            return s

    def packtabs(self, s, tabsize = 8):
        if tabsize > 0:
            sb = _io.StringIO()
            for i in range(0, len(s), tabsize):
                c = s[i:i + tabsize]
                cr = c.rstrip(" ")
                if c != cr: ## Spaces at the end of a section
                    sb.write(cr + "\t") ## replace by tab
                else:
                    sb.write(c)
            return sb.getvalue()
        else:
            return s

    def cls(self):
        self.wr(b"\x1b[2J")




