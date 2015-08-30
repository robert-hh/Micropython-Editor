
## this is still syntactically correct python code, even if it is never executed.
##
##
## This is the regex version of find.
    def find_in_file(self, pattern, pos):
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
        for line in range(self.cur_line, self.total_lines):
            if self.case == "y":
                match = rex.search(self.content[line][spos:])
            else:
                match = rex.search(self.content[line][spos:].lower())
            if match:
                break
            spos = 0
        else:
            self.message = pattern + " not found"
            return 0
## micropython does not support span(), therefore a second simple find on the target line
        if self.case == "y":
            self.col = max(self.content[line][spos:].find(match.group(0)), 0) + spos
        else:
            self.col = max(self.content[line][spos:].lower().find(match.group(0)), 0) + spos
        self.cur_line = line
        self.message = ' ' ## force status once
        return len(match.group(0))

    def push_msg(self, msg): ## Write a message and place cursor back
        self.wr("\x1b[s")  ## Push curseo
        self.wr(msg)
        self.wr("\x1b[u")  ## Pop Cursor

    def line_edit(self, prompt, default):  ## better one: added cursor keys and backsp, delete
        self.goto(self.height, 0)
        self.hilite(True)
        self.wr(prompt)
        self.clear_to_eol()
        res = default
        self.message = ' ' # Shows status after lineedit
        pos = 0
        self.push_msg(res) 
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
            elif key == KEY_BACKSPACE: ## Backspace
                if pos > 0:
                    res = res[:pos-1] + res[pos:]
                    self.wr("\b")
                    pos -= 1
                    self.push_msg(res[pos:] + ' ') ## Push + pop cursor
            elif key == KEY_DELETE: ## Delete
                if pos < len(res):
                    res = res[:pos] + res[pos+1:]
                    self.push_msg(res[pos:] + ' ') ## Push + pop cursor
            elif 0x20 <= key < 0x100: ## char to be inserted
                if len(prompt) + len(res) < self.width - 2:
                    res = res[:pos] + chr(key) + res[pos:]
                    self.wr(res[pos])
                    pos += 1
                    self.push_msg(res[pos:]) ## Push + pop cursor
            else:  ## ignore everything else
                pass



    def expandtabs(s, tabsize = 8):
        import _io
        if '\t' in s:
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


